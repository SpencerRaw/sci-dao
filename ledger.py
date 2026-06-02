"""
Contribution Ledger v0 — immutable, Git-like contribution tracking.
Every data point traces back to the human who made it.
No blockchain needed — JSON + content hashing for integrity.
"""

import json
import hashlib
import time
import os
from pathlib import Path
from typing import Optional


LEDGER_DIR = Path(__file__).parent / "ledger"


class ContributionLedger:
    """
    Immutable contribution record.
    
    Each entry:
    - id: unique hash-based identifier
    - timestamp: when recorded
    - contributor_id: who did the work
    - task_id: which task was completed
    - hypothesis_id: which hypothesis this serves
    - data_type: RAW_DATA | ANALYSIS | INSIGHT | REVIEW
    - content_hash: SHA256 of submitted content
    - content_path: path to stored result file
    - parent_entry_id: previous related entry (for provenance chain)
    - weight: contribution weight (0.0-1.0)
    """
    
    def __init__(self, path: Path = LEDGER_DIR):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.entries_file = self.path / "entries.jsonl"
        self.contributors_file = self.path / "contributors.json"
        
        self.entries: list[dict] = []
        self.contributors: dict[str, dict] = {}
        self._load()
    
    def _load(self):
        if self.entries_file.exists():
            with open(self.entries_file) as f:
                self.entries = [json.loads(line) for line in f if line.strip()]
        if self.contributors_file.exists():
            with open(self.contributors_file) as f:
                self.contributors = json.load(f)
    
    def _save(self):
        with open(self.entries_file, "w") as f:
            for e in self.entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        with open(self.contributors_file, "w") as f:
            json.dump(self.contributors, f, indent=2, ensure_ascii=False)
    
    def register_contributor(self, name: str, skills: list[str] = None,
                            equipment: list[str] = None) -> str:
        """Register a new contributor. Returns contributor ID."""
        cid = f"CTRB-{hashlib.sha256(name.encode()).hexdigest()[:8]}"
        self.contributors[cid] = {
            "id": cid,
            "name": name,
            "skills": skills or [],
            "equipment": equipment or [],
            "joined_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_contributions": 0,
            "total_weight": 0.0,
            "completed_tasks": []
        }
        self._save()
        return cid
    
    def record(self, contributor_id: str, task_id: str, hypothesis_id: str,
               content: str, data_type: str = "RAW_DATA",
               parent_entry_id: str = None, weight: float = 0.1) -> str:
        """
        Record a contribution. Returns entry ID.
        
        Args:
            contributor_id: Who did the work
            task_id: Which task
            hypothesis_id: Which hypothesis
            content: The actual result (text/JSON/description)
            data_type: RAW_DATA | ANALYSIS | INSIGHT | REVIEW
            parent_entry_id: Previous related entry
            weight: Contribution weight (0.0-1.0)
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        entry = {
            "id": f"ENT-{content_hash[:12]}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "contributor_id": contributor_id,
            "task_id": task_id,
            "hypothesis_id": hypothesis_id,
            "data_type": data_type,
            "content_hash": content_hash,
            "content_preview": content[:200],
            "parent_entry_id": parent_entry_id,
            "weight": weight
        }
        
        self.entries.append(entry)
        
        # Store full content separately
        content_path = self.path / "results" / f"{entry['id']}.txt"
        content_path.parent.mkdir(exist_ok=True)
        content_path.write_text(content)
        entry["content_path"] = str(content_path)
        
        # Update contributor stats
        if contributor_id in self.contributors:
            c = self.contributors[contributor_id]
            c["total_contributions"] += 1
            c["total_weight"] += weight
            if task_id not in c["completed_tasks"]:
                c["completed_tasks"].append(task_id)
        
        self._save()
        return entry["id"]
    
    def get_contributor_summary(self, contributor_id: str) -> dict:
        """Get a contributor's record."""
        c = self.contributors.get(contributor_id, {})
        entries = [e for e in self.entries if e["contributor_id"] == contributor_id]
        return {
            **c,
            "entry_count": len(entries),
            "recent_entries": entries[-5:]
        }
    
    def get_hypothesis_lineage(self, hypothesis_id: str) -> list[dict]:
        """Get all contributions for a hypothesis, ordered by time."""
        return sorted(
            [e for e in self.entries if e["hypothesis_id"] == hypothesis_id],
            key=lambda e: e["timestamp"]
        )
    
    def get_leaderboard(self) -> list[dict]:
        """Contributors ranked by total weight."""
        ranked = sorted(
            self.contributors.values(),
            key=lambda c: c["total_weight"],
            reverse=True
        )
        return [{"name": c["name"], "weight": round(c["total_weight"], 3),
                 "contributions": c["total_contributions"]} for c in ranked]
    
    def verify_integrity(self, entry_id: str) -> bool:
        """Verify an entry's content hasn't been tampered with."""
        for e in self.entries:
            if e["id"] == entry_id:
                content_path = e.get("content_path", "")
                if content_path and os.path.exists(content_path):
                    current_content = Path(content_path).read_text()
                    current_hash = hashlib.sha256(current_content.encode()).hexdigest()
                    return current_hash == e["content_hash"]
        return False


if __name__ == "__main__":
    # Demo
    ledger = ContributionLedger()
    
    # Register contributors
    alice = ledger.register_contributor("Alice Chen", 
        skills=["cell culture", "MTT assay", "Western blot"],
        equipment=["Biosafety cabinet", "Plate reader"])
    
    bob = ledger.register_contributor("Bob Wang",
        skills=["PCR", "qPCR", "RNA extraction"],
        equipment=["Thermocycler", "qPCR machine"])
    
    # Record a contribution
    ledger.record(
        contributor_id=alice,
        task_id="TASK-001",
        hypothesis_id="HYP-001",
        content="MTT assay results: HeLa cells treated with 50μg/ml NIR-CD for 24h. "
                "Viability: 45% ± 5% (n=3). IC50 estimated at 42μg/ml.",
        data_type="RAW_DATA",
        weight=0.15
    )
    
    ledger.record(
        contributor_id=bob,
        task_id="TASK-002",
        hypothesis_id="HYP-001",
        content="qPCR results: Caspase-3 mRNA upregulated 3.2-fold (p<0.01). "
                "Bax/Bcl-2 ratio increased 2.8-fold. Confirms apoptosis pathway.",
        data_type="RAW_DATA",
        weight=0.15
    )
    
    print("=== Leaderboard ===")
    print(json.dumps(ledger.get_leaderboard(), indent=2))
    
    print("\n=== Hypothesis Lineage ===")
    print(json.dumps(ledger.get_hypothesis_lineage("HYP-001"), indent=2))
