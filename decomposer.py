"""
Task Decomposer v0 — atomizes scientific hypotheses into executable tasks.
Each task is small enough for one person to execute with standard lab equipment.
Uses the standalone scidao.llm client.
"""

import json
from scidao.llm import call_llm


def decompose_hypothesis(hypothesis: dict, domain: str) -> list[dict]:
    """
    Break a hypothesis into atomized, executable experiment tasks.

    Each task includes:
    - id: unique identifier
    - title: one-line description
    - description: what to do and why
    - materials: required reagents/equipment
    - steps: numbered protocol
    - expected_result: what success looks like
    - time_estimate: hours
    - difficulty: BEGINNER | INTERMEDIATE | EXPERT
    - dependencies: list of task IDs that must complete first
    """
    title = hypothesis.get("title", "")
    text = hypothesis.get("text", "")
    hypo_id = hypothesis.get("id", "UNKNOWN")
    
    prompt = f"""You are a senior lab manager breaking down a research hypothesis into 
atomized, executable experiments. Each task must be small enough for ONE person 
to complete with standard lab equipment.

Research Domain: {domain}

Hypothesis: {title}
{text}

Your job: Decompose this hypothesis into 3-5 CONCRETE experiment tasks.
Each task should be so specific that a competent research assistant could execute it
without further clarification.

For EACH task, provide:
1. title: Short, action-oriented (e.g. "MTT cytotoxicity assay on HeLa cells")
2. description: 1-2 sentences on what and why
3. materials: List specific reagents, concentrations, equipment
4. steps: Numbered protocol (at least 3 steps, maximum 8)
5. expected_result: Observable outcome if hypothesis is correct
6. time_estimate: Hours (integer, 1-40)
7. difficulty: BEGINNER | INTERMEDIATE | EXPERT
8. dependencies: List of prerequisite task titles (empty list if none)

CRITICAL: 
- Use specific concentrations, cell lines, incubation times
- Each task must produce OBSERVABLE data (numbers, images, measurements)
- Tasks should be INDEPENDENT where possible
- Beginner = standard lab techniques (pipetting, cell culture, basic assays)
- Expert = specialized techniques (cryo-EM, patch clamp, in vivo surgery)

Return as JSON array."""
    
    response = call_llm(prompt, temperature=0.5)
    
    try:
        cleaned = response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        if "[" in cleaned:
            cleaned = cleaned[cleaned.index("["):cleaned.rindex("]")+1]
        tasks = json.loads(cleaned)
    except json.JSONDecodeError:
        tasks = [{"title": "Parse Error", "description": response[:500],
                  "materials": [], "steps": [], "expected_result": "N/A",
                  "time_estimate": 0, "difficulty": "UNKNOWN", "dependencies": []}]
    
    # Add IDs and link to parent hypothesis
    for i, task in enumerate(tasks):
        task["id"] = f"TASK-{hypo_id}-{i+1:02d}"
        task["parent_hypothesis"] = hypo_id
        task["status"] = "OPEN"  # OPEN | CLAIMED | COMPLETED | VERIFIED
        task["assignee"] = None
        task["result_summary"] = None
    
    return tasks


def estimate_effort(tasks: list[dict]) -> dict:
    """Summarize the total effort for a set of tasks."""
    total_hours = sum(t.get("time_estimate", 0) for t in tasks)
    difficulty_counts = {"BEGINNER": 0, "INTERMEDIATE": 0, "EXPERT": 0, "UNKNOWN": 0}
    for t in tasks:
        diff = t.get("difficulty", "UNKNOWN")
        if diff in difficulty_counts:
            difficulty_counts[diff] += 1
    
    return {
        "total_tasks": len(tasks),
        "total_hours": total_hours,
        "difficulty_breakdown": difficulty_counts,
        "estimated_cost": f"${total_hours * 50}-${total_hours * 150}"  # rough CRO pricing
    }


if __name__ == "__main__":
    # Quick test
    test_hypo = {
        "id": "HYP-001",
        "title": "NIR carbon dots upregulate photosynthetic genes in Arabidopsis",
        "text": "Carbon dots with NIR emission (700-900nm) act as artificial antenna complexes, "
                "transferring energy to Photosystem II and upregulating LHCB and PSBA genes "
                "under low-light conditions."
    }
    tasks = decompose_hypothesis(test_hypo, "NIR carbon dots for plant growth")
    print(json.dumps(tasks, indent=2, ensure_ascii=False))
    print("\n--- Effort Estimate ---")
    print(json.dumps(estimate_effort(tasks), indent=2))
