"""
SciDAO Server — FastAPI REST API + Web UI.

Run: scidao serve
  or: uvicorn scidao.server:app --reload
"""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scidao.curiosity import generate_hypotheses
from scidao.decomposer import decompose_hypothesis
from scidao.ledger import ContributionLedger
from scidao.learner import refine_hypothesis

app = FastAPI(
    title="SciDAO",
    description="AI Scientist × Human Lab Network",
    version="0.3.0",
)


# ── Pydantic models ────────────────────────────────────────────

class ExploreRequest(BaseModel):
    domain: str
    constraints: str = ""

class RegisterRequest(BaseModel):
    name: str
    skills: str = ""

class SubmitRequest(BaseModel):
    contributor_id: str
    task_id: str
    hypothesis_id: str
    result: str
    domain: str = ""

class ClaimRequest(BaseModel):
    contributor_id: str


# ── Helpers ────────────────────────────────────────────────────

def _get_ledger():
    return ContributionLedger()

def _load_marketplace():
    mp = Path("output/marketplace.json")
    if mp.exists():
        return json.loads(mp.read_text())
    return None


# ── UI ─────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the demo UI."""
    demo = Path(__file__).parent.parent / "demo.html"
    if demo.exists():
        return demo.read_text()
    return "<h1>SciDAO Server Running</h1><p>demo.html not found</p>"


# ── Health ─────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    ledger = _get_ledger()
    mp = _load_marketplace()
    return {
        "status": "ok",
        "hypotheses": len(ledger.hypotheses),
        "contributors": len(ledger.contributors),
        "marketplace": bool(mp),
    }


# ── Hypotheses ─────────────────────────────────────────────────

@app.get("/api/hypotheses")
def list_hypotheses():
    ledger = _get_ledger()
    result = []
    for hid, h in ledger.hypotheses.items():
        refs = ledger.get_refinements_for(hid)
        result.append({
            "id": hid,
            "title": h.get("title", ""),
            "text": h.get("text", "")[:300],
            "testability": h.get("testability", "?"),
            "domain": h.get("domain", ""),
            "refinements": len(refs),
            "latest_verdict": refs[-1]["verdict"] if refs else None,
            "latest_confidence": refs[-1]["confidence"] if refs else None,
        })
    return result


@app.get("/api/hypotheses/{hypothesis_id}")
def get_hypothesis(hypothesis_id: str):
    ledger = _get_ledger()
    h = ledger.get_hypothesis(hypothesis_id)
    if not h:
        raise HTTPException(404, "Hypothesis not found")
    refs = ledger.get_refinements_for(hypothesis_id)
    lineage = ledger.get_hypothesis_lineage(hypothesis_id)
    return {
        "hypothesis": dict(h),
        "refinements": refs,
        "contributions": lineage,
        "refinement_count": len(refs),
    }


# ── Tasks ──────────────────────────────────────────────────────

@app.get("/api/tasks")
def list_tasks(status: str = None):
    mp = _load_marketplace()
    if not mp:
        return {"tasks": [], "stats": {}}
    tasks = mp.get("tasks", [])
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return {"tasks": tasks, "stats": mp.get("stats", {})}


@app.post("/api/tasks/{task_id}/claim")
def claim_task(task_id: str, req: ClaimRequest):
    mp = _load_marketplace()
    if not mp:
        raise HTTPException(404, "No marketplace data")
    
    for t in mp["tasks"]:
        if t["id"] == task_id:
            if t.get("status") != "OPEN":
                raise HTTPException(409, f"Task is {t.get('status')}")
            t["status"] = "CLAIMED"
            t["assignee"] = req.contributor_id
            Path("output").mkdir(exist_ok=True)
            Path("output/marketplace.json").write_text(
                json.dumps(mp, indent=2, ensure_ascii=False)
            )
            return {"status": "claimed", "task_id": task_id, "assignee": req.contributor_id}
    
    raise HTTPException(404, "Task not found")


@app.post("/api/tasks/{task_id}/verify")
def verify_task(task_id: str, req: ClaimRequest):
    mp = _load_marketplace()
    if not mp:
        raise HTTPException(404, "No marketplace data")
    
    for t in mp["tasks"]:
        if t["id"] == task_id:
            if t.get("status") != "COMPLETED":
                raise HTTPException(409, f"Task must be COMPLETED, is {t.get('status')}")
            t["status"] = "VERIFIED"
            Path("output/marketplace.json").write_text(
                json.dumps(mp, indent=2, ensure_ascii=False)
            )
            return {"status": "verified", "task_id": task_id}
    
    raise HTTPException(404, "Task not found")


# ── Explore ────────────────────────────────────────────────────

@app.post("/api/explore")
def api_explore(req: ExploreRequest):
    hypos = generate_hypotheses(req.domain, req.constraints, num=5)
    ledger = _get_ledger()
    ledger.store_hypotheses(hypos, req.domain)
    return {"hypotheses": hypos, "count": len(hypos)}


# ── Contributors ───────────────────────────────────────────────

@app.post("/api/contributors")
def register_contributor(req: RegisterRequest):
    ledger = _get_ledger()
    skills = [s.strip() for s in req.skills.split(",") if s.strip()]
    cid = ledger.register_contributor(req.name, skills=skills)
    return {"contributor_id": cid, "name": req.name}


@app.get("/api/contributors")
def list_contributors():
    ledger = _get_ledger()
    return {"contributors": list(ledger.contributors.values())}


# ── Submit (with feedback loop) ────────────────────────────────

@app.post("/api/submit")
def submit_result(req: SubmitRequest):
    ledger = _get_ledger()
    
    if req.contributor_id not in ledger.contributors:
        raise HTTPException(400, f"Unknown contributor: {req.contributor_id}")
    
    # Record
    entry_id = ledger.record(
        contributor_id=req.contributor_id,
        task_id=req.task_id,
        hypothesis_id=req.hypothesis_id,
        content=req.result,
        data_type="RAW_DATA",
        weight=0.15,
    )
    
    # Mark task as COMPLETED in marketplace
    mp = _load_marketplace()
    if mp:
        for t in mp.get("tasks", []):
            if t["id"] == req.task_id:
                t["status"] = "COMPLETED"
                Path("output/marketplace.json").write_text(
                    json.dumps(mp, indent=2, ensure_ascii=False)
                )
                break
    
    # Feedback loop
    refinement = None
    if req.domain:
        hypothesis = ledger.get_hypothesis(req.hypothesis_id)
        if hypothesis:
            previous = ledger.get_hypothesis_lineage(req.hypothesis_id)
            previous_results = [e for e in previous if e.get("data_type") == "RAW_DATA"]
            refinement = refine_hypothesis(hypothesis, req.result, req.domain, previous_results)
            ledger.store_refinement(req.hypothesis_id, refinement)
    
    return {
        "entry_id": entry_id,
        "refinement": refinement,
    }


# ── Leaderboard ────────────────────────────────────────────────

@app.get("/api/leaderboard")
def leaderboard():
    ledger = _get_ledger()
    return {"leaderboard": ledger.get_leaderboard()}


# ── Lineage ─────────────────────────────────────────────────────

@app.get("/api/lineage/{hypothesis_id}")
def lineage(hypothesis_id: str):
    ledger = _get_ledger()
    h = ledger.get_hypothesis(hypothesis_id)
    if not h:
        raise HTTPException(404, "Hypothesis not found")
    return {
        "hypothesis": dict(h),
        "contributions": ledger.get_hypothesis_lineage(hypothesis_id),
        "refinements": ledger.get_refinements_for(hypothesis_id),
    }


# ── CLI entry ──────────────────────────────────────────────────

def serve(host: str = "0.0.0.0", port: int = 8000):
    """Run the SciDAO server."""
    import uvicorn
    print(f"""
╔══════════════════════════════════════════════════════╗
║  🧬 SciDAO Server v0.3                              ║
║  API: http://{host}:{port}                               ║
║  Docs: http://{host}:{port}/docs                          ║
╚══════════════════════════════════════════════════════╝
""")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    serve()
