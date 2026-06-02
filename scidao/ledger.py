"""
Contribution Ledger v1 — immutable, SQLite-backed contribution tracking.
Every data point traces back to the human who made it.
SQLite for queryability + concurrency safety. No blockchain needed.
"""

import json
import hashlib
import sqlite3
import time
import os
from pathlib import Path
from typing import Optional


LEDGER_DIR = Path("ledger_data")  # relative to cwd, overridable in __init__


class ContributionLedger:
    """
    Immutable contribution record backed by SQLite.

    Tables:
    - contributors: registered researchers
    - entries: immutable contribution records
    - hypotheses: stored hypotheses for refinement
    - refinements: versioned hypothesis updates
    """

    def __init__(self, path: Path = LEDGER_DIR):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.path / "scidao.db"
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self):
        """Create tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS contributors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                skills TEXT DEFAULT '[]',
                equipment TEXT DEFAULT '[]',
                joined_at TEXT NOT NULL,
                total_contributions INTEGER DEFAULT 0,
                total_weight REAL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                contributor_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                hypothesis_id TEXT NOT NULL,
                data_type TEXT DEFAULT 'RAW_DATA',
                content_hash TEXT NOT NULL,
                content_preview TEXT DEFAULT '',
                parent_entry_id TEXT,
                weight REAL DEFAULT 0.1,
                FOREIGN KEY (contributor_id) REFERENCES contributors(id)
            );

            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                text TEXT DEFAULT '',
                rationale TEXT DEFAULT '',
                testability TEXT DEFAULT 'UNKNOWN',
                domain TEXT DEFAULT '',
                data TEXT DEFAULT '{}',
                stored_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS refinements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hypothesis_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                verdict TEXT DEFAULT 'INCONCLUSIVE',
                confidence REAL DEFAULT 0.5,
                refined_title TEXT DEFAULT '',
                refined_text TEXT DEFAULT '',
                learning TEXT DEFAULT '',
                next_step TEXT DEFAULT '',
                refined_at TEXT NOT NULL,
                FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                hypothesis_id TEXT NOT NULL,
                status TEXT DEFAULT 'OPEN',
                assignee TEXT,
                claimed_at TEXT,
                submitted_at TEXT,
                verified_at TEXT,
                claim_expiry TEXT,
                FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
            );

            CREATE INDEX IF NOT EXISTS idx_entries_hypothesis 
                ON entries(hypothesis_id);
            CREATE INDEX IF NOT EXISTS idx_entries_contributor 
                ON entries(contributor_id);
            CREATE INDEX IF NOT EXISTS idx_refinements_hypothesis 
                ON refinements(hypothesis_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_hypothesis 
                ON tasks(hypothesis_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status 
                ON tasks(status);
        """)
        self._conn.commit()

    # ── Properties for backward compat ─────────────────────────

    @property
    def entries(self) -> list[dict]:
        """Compatibility: return all entries as list of dicts."""
        rows = self._conn.execute(
            "SELECT * FROM entries ORDER BY timestamp"
        ).fetchall()
        return [dict(r) for r in rows]

    @property
    def contributors(self) -> dict[str, dict]:
        """Compatibility: return contributors as dict keyed by ID."""
        rows = self._conn.execute("SELECT * FROM contributors").fetchall()
        result = {}
        for r in rows:
            d = dict(r)
            d["skills"] = json.loads(d.get("skills", "[]"))
            d["equipment"] = json.loads(d.get("equipment", "[]"))
            d["completed_tasks"] = json.loads(
                d.get("completed_tasks", "[]")
            )
            result[d["id"]] = d
        return result

    @property
    def hypotheses(self) -> dict[str, dict]:
        """Compatibility: return hypotheses as dict keyed by ID."""
        rows = self._conn.execute("SELECT * FROM hypotheses").fetchall()
        return {r["id"]: dict(r) for r in rows}

    @property
    def refinements(self) -> list[dict]:
        """Compatibility: return all refinements."""
        rows = self._conn.execute(
            "SELECT * FROM refinements ORDER BY version"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Contributor management ─────────────────────────────────

    def register_contributor(self, name: str, skills: list[str] = None,
                            equipment: list[str] = None) -> str:
        """Register a new contributor. Returns contributor ID."""
        cid = f"CTRB-{hashlib.sha256(name.encode()).hexdigest()[:8]}"
        self._conn.execute(
            """INSERT OR IGNORE INTO contributors 
               (id, name, skills, equipment, joined_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                cid, name,
                json.dumps(skills or []),
                json.dumps(equipment or []),
                time.strftime("%Y-%m-%dT%H:%M:%S"),
            ),
        )
        self._conn.commit()
        return cid

    # ── Entry recording ────────────────────────────────────────

    def record(self, contributor_id: str, task_id: str, hypothesis_id: str,
               content: str, data_type: str = "RAW_DATA",
               parent_entry_id: str = None, weight: float = 0.1) -> str:
        """
        Record a contribution. Returns entry ID.
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        entry_id = f"ENT-{content_hash[:12]}"

        self._conn.execute(
            """INSERT OR IGNORE INTO entries
               (id, timestamp, contributor_id, task_id, hypothesis_id,
                data_type, content_hash, content_preview, parent_entry_id, weight)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry_id,
                time.strftime("%Y-%m-%dT%H:%M:%S"),
                contributor_id,
                task_id,
                hypothesis_id,
                data_type,
                content_hash,
                content[:200],
                parent_entry_id,
                weight,
            ),
        )

        # Store full content as a file for integrity verification
        content_path = self.path / "results" / f"{entry_id}.txt"
        content_path.parent.mkdir(exist_ok=True)
        content_path.write_text(content)

        # Update contributor stats
        self._conn.execute(
            """UPDATE contributors 
               SET total_contributions = total_contributions + 1,
                   total_weight = total_weight + ?
               WHERE id = ?""",
            (weight, contributor_id),
        )
        self._conn.commit()
        return entry_id

    # ── Queries ────────────────────────────────────────────────

    def get_contributor_summary(self, contributor_id: str) -> dict:
        """Get a contributor's record."""
        c = self._conn.execute(
            "SELECT * FROM contributors WHERE id = ?", (contributor_id,)
        ).fetchone()
        if not c:
            return {}
        d = dict(c)
        d["skills"] = json.loads(d.get("skills", "[]"))
        d["equipment"] = json.loads(d.get("equipment", "[]"))
        entries = self._conn.execute(
            "SELECT * FROM entries WHERE contributor_id = ? ORDER BY timestamp DESC LIMIT 5",
            (contributor_id,),
        ).fetchall()
        d["recent_entries"] = [dict(e) for e in entries]
        return d

    def get_hypothesis_lineage(self, hypothesis_id: str) -> list[dict]:
        """Get all contributions for a hypothesis, ordered by time."""
        rows = self._conn.execute(
            "SELECT * FROM entries WHERE hypothesis_id = ? ORDER BY timestamp",
            (hypothesis_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_leaderboard(self) -> list[dict]:
        """Contributors ranked by total weight."""
        rows = self._conn.execute(
            """SELECT name, total_weight as weight, total_contributions as contributions
               FROM contributors ORDER BY total_weight DESC"""
        ).fetchall()
        return [
            {"name": r["name"], "weight": round(r["weight"], 3),
             "contributions": r["contributions"]}
            for r in rows
        ]

    def verify_integrity(self, entry_id: str) -> bool:
        """Verify an entry's content hasn't been tampered with."""
        row = self._conn.execute(
            "SELECT content_hash FROM entries WHERE id = ?", (entry_id,)
        ).fetchone()
        if not row:
            return False
        content_path = self.path / "results" / f"{entry_id}.txt"
        if content_path.exists():
            current = content_path.read_text()
            current_hash = hashlib.sha256(current.encode()).hexdigest()
            return current_hash == row["content_hash"]
        return False

    # ── Hypothesis storage ────────────────────────────────────

    def store_hypotheses(self, hypotheses: list[dict], domain: str):
        """Store generated hypotheses for later retrieval and refinement."""
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        for h in hypotheses:
            hid = h.get("id", "")
            if not hid:
                continue
            self._conn.execute(
                """INSERT OR REPLACE INTO hypotheses
                   (id, title, text, rationale, testability, domain, data, stored_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    hid,
                    h.get("title", ""),
                    h.get("text", ""),
                    h.get("rationale", ""),
                    h.get("testability", "UNKNOWN"),
                    domain,
                    json.dumps(h, ensure_ascii=False),
                    now,
                ),
            )
        self._conn.commit()

    def get_hypothesis(self, hypothesis_id: str) -> dict | None:
        """Retrieve a stored hypothesis by ID."""
        row = self._conn.execute(
            "SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Refinement tracking ───────────────────────────────────

    def store_refinement(self, hypothesis_id: str, refined: dict):
        """Record a hypothesis refinement with version tracking."""
        version = self.get_refinement_count(hypothesis_id) + 1
        self._conn.execute(
            """INSERT INTO refinements
               (hypothesis_id, version, verdict, confidence,
                refined_title, refined_text, learning, next_step, refined_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                hypothesis_id,
                version,
                refined.get("verdict", "?"),
                refined.get("confidence", 0.5),
                refined.get("refined_title", ""),
                refined.get("refined_text", ""),
                refined.get("learning", ""),
                refined.get("next_step", ""),
                refined.get("refined_at", time.strftime("%Y-%m-%dT%H:%M:%S")),
            ),
        )
        self._conn.commit()

    def get_refinement_count(self, hypothesis_id: str) -> int:
        """How many times has this hypothesis been refined?"""
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM refinements WHERE hypothesis_id = ?",
            (hypothesis_id,),
        ).fetchone()
        return row["cnt"] if row else 0

    def get_refinements_for(self, hypothesis_id: str) -> list[dict]:
        """Get all refinements for a hypothesis, ordered by version."""
        rows = self._conn.execute(
            "SELECT * FROM refinements WHERE hypothesis_id = ? ORDER BY version",
            (hypothesis_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_refinements(self) -> list[dict]:
        """Get all refinements across all hypotheses."""
        rows = self._conn.execute(
            "SELECT * FROM refinements ORDER BY refined_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Task lifecycle ─────────────────────────────────────────

    def store_tasks(self, tasks: list[dict]):
        """Store tasks from the decomposer into the ledger."""
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        for t in tasks:
            self._conn.execute(
                """INSERT OR REPLACE INTO tasks
                   (id, title, hypothesis_id, status)
                   VALUES (?, ?, ?, ?)""",
                (t.get("id", ""), t.get("title", ""),
                 t.get("parent_hypothesis", ""), t.get("status", "OPEN")),
            )
        self._conn.commit()

    def claim_task(self, task_id: str, contributor_id: str) -> dict:
        """Claim an OPEN task. Sets CLAIMED with 48h expiry."""
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Task not found: {task_id}")
        if row["status"] != "OPEN":
            raise ValueError(f"Task is {row['status']}, not OPEN")
        if row["claim_expiry"] and row["claim_expiry"] > time.strftime("%Y-%m-%dT%H:%M:%S"):
            raise ValueError(f"Task claimed until {row['claim_expiry']}")

        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        # 48h from now
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%S")

        self._conn.execute(
            """UPDATE tasks SET status='CLAIMED', assignee=?, 
               claimed_at=?, claim_expiry=? WHERE id=?""",
            (contributor_id, now, expiry, task_id),
        )
        self._conn.commit()
        return {"task_id": task_id, "status": "CLAIMED", "assignee": contributor_id,
                "expires": expiry}

    def submit_task_result(self, task_id: str, content: str) -> dict:
        """Mark a claimed task as submitted."""
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Task not found: {task_id}")
        if row["status"] != "CLAIMED":
            raise ValueError(f"Task is {row['status']}, not CLAIMED")

        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._conn.execute(
            "UPDATE tasks SET status='SUBMITTED', submitted_at=? WHERE id=?",
            (now, task_id),
        )
        self._conn.commit()
        return {"task_id": task_id, "status": "SUBMITTED"}

    def verify_task(self, task_id: str) -> dict:
        """Verify a submitted task."""
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Task not found: {task_id}")
        if row["status"] != "SUBMITTED":
            raise ValueError(f"Task is {row['status']}, not SUBMITTED")

        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._conn.execute(
            "UPDATE tasks SET status='VERIFIED', verified_at=? WHERE id=?",
            (now, task_id),
        )
        self._conn.commit()
        return {"task_id": task_id, "status": "VERIFIED"}

    def get_claimable_tasks(self) -> list[dict]:
        """Get all OPEN tasks (not yet claimed)."""
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE status='OPEN' ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by ID."""
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Cleanup ────────────────────────────────────────────────

    def close(self):
        self._conn.close()

    def __del__(self):
        try:
            self._conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Demo
    import shutil, tempfile

    tmp = Path(tempfile.mkdtemp())
    ledger = ContributionLedger(path=tmp)

    # Register contributors
    alice = ledger.register_contributor("Alice Chen",
        skills=["cell culture", "MTT assay", "Western blot"],
        equipment=["Biosafety cabinet", "Plate reader"])

    bob = ledger.register_contributor("Bob Wang",
        skills=["PCR", "qPCR", "RNA extraction"],
        equipment=["Thermocycler", "qPCR machine"])

    # Store hypothesis
    ledger.store_hypotheses([{
        "id": "HYP-001",
        "title": "NIR carbon dots upregulate photosynthetic genes",
        "text": "CDs with NIR emission act as artificial antenna complexes.",
        "testability": "HIGH",
        "rationale": "FRET from CDs to PSII",
    }], "carbon dots for plant growth")

    # Record contributions
    ledger.record(
        contributor_id=alice,
        task_id="TASK-001",
        hypothesis_id="HYP-001",
        content="MTT assay: HeLa cells treated with 50μg/ml NIR-CD for 24h. "
                "Viability: 45% ± 5% (n=3). IC50 estimated at 42μg/ml.",
        data_type="RAW_DATA",
        weight=0.15,
    )

    # Refine
    ledger.store_refinement("HYP-001", {
        "verdict": "SUPPORTS",
        "confidence": 0.82,
        "refined_title": "NIR CDs enhance PSII via FRET under low light",
        "learning": "Confirmed upregulation under 50 μmol/m²/s",
        "next_step": "Test with phyB mutant to rule out shade response",
    })

    print("=== Leaderboard ===")
    for entry in ledger.get_leaderboard():
        print(f"  {entry['name']}: {entry['weight']:.3f} ({entry['contributions']} contribs)")

    print("\n=== Hypothesis ===")
    h = ledger.get_hypothesis("HYP-001")
    print(f"  {h['id']}: {h['title'][:60]}...")

    print("\n=== Refinements ===")
    for r in ledger.get_refinements_for("HYP-001"):
        print(f"  v{r['version']} [{r['verdict']}] conf={r['confidence']}: {r['learning'][:80]}")

    # Cleanup
    ledger.close()
    shutil.rmtree(tmp)
    print("\n✅ SQLite ledger demo complete")
