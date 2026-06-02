"""
Learner v0 — the feedback loop that makes SciDAO a learning system.

After a human submits experimental results, the AI:
1. Evaluates the result against the original hypothesis
2. Refines the hypothesis based on what we learned
3. Adjusts confidence scores
4. Suggests the next experiment
"""

import json
from scidao.llm import call_llm


def refine_hypothesis(
    hypothesis: dict,
    result: str,
    domain: str,
    previous_results: list[dict] = None,
) -> dict:
    """
    Feed experimental results back to the AI. Returns refined hypothesis.

    Args:
        hypothesis: Original hypothesis dict with title, text, rationale
        result: The experimental result (text/JSON/description)
        domain: Research domain
        previous_results: List of prior results for this hypothesis (for context)

    Returns:
        Dict with verdict, confidence, refined hypothesis, learning, next_step
    """
    title = hypothesis.get("title", "")
    text = hypothesis.get("text", "")
    hypo_id = hypothesis.get("id", "?")

    # Build context from previous results
    history = ""
    if previous_results:
        history = "\n\nPrevious results for this hypothesis:\n"
        for i, r in enumerate(previous_results, 1):
            history += f"  Round {i}: {r.get('content_preview', r.get('content', ''))[:300]}\n"

    prompt = f"""You are an AI scientist reviewing experimental results and updating your understanding.

Research Domain: {domain}

Your Original Hypothesis [{hypo_id}]:
{title}
{text}
{history}

NEW Experimental Result:
{result}

Your task as a learning scientist:
1. **Verdict**: Does this result SUPPORT, REFUTE, or is it INCONCLUSIVE for the hypothesis?
2. **Refine**: How should the hypothesis change based on this new evidence?
   - If SUPPORTS: strengthen the claim, narrow the scope, increase specificity
   - If REFUTES: identify which assumption failed, propose an alternative mechanism
   - If INCONCLUSIVE: identify the ambiguity, suggest better controls
3. **Confidence**: Assign a confidence score (0.0 = disproven, 0.5 = uncertain, 1.0 = strongly supported)
4. **Learning**: One sentence on what we learned from this result
5. **Next Step**: What experiment should we run next? Be specific.

CRITICAL:
- Be honest — if the result contradicts your hypothesis, say so. Don't force-fit.
- If the result is ambiguous, identify the exact source of ambiguity.
- Propose concrete next experiments with specific methods.

Return as JSON:
{{"verdict": "SUPPORTS|REFUTES|INCONCLUSIVE",
  "confidence": 0.0-1.0,
  "refined_title": "updated hypothesis title",
  "refined_text": "updated hypothesis description with rationale",
  "learning": "one sentence on what we learned",
  "next_step": "specific next experiment to run"}}"""

    response = call_llm(prompt, temperature=0.4)

    try:
        cleaned = response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        if "{" in cleaned and "}" in cleaned:
            cleaned = cleaned[cleaned.index("{"):cleaned.rindex("}") + 1]
        refined = json.loads(cleaned)
    except json.JSONDecodeError:
        refined = {
            "verdict": "INCONCLUSIVE",
            "confidence": 0.5,
            "refined_title": title,
            "refined_text": text,
            "learning": "Failed to parse LLM refinement output",
            "next_step": "Re-run experiment with better controls",
        }

    refined["original_hypothesis_id"] = hypo_id
    refined["refined_at"] = _now()
    return refined


def analyze_across_hypotheses(
    refinements: list[dict],
    domain: str,
) -> dict:
    """
    After refining multiple hypotheses, look for patterns across them.
    Returns meta-insights about the research direction.
    """
    if len(refinements) < 2:
        return {"patterns": [], "recommendation": "Need at least 2 refinements to find patterns"}

    summary = "\n".join(
        f"[{r.get('original_hypothesis_id', '?')}] {r.get('verdict')}: {r.get('learning', '')}"
        for r in refinements
    )

    prompt = f"""You are a principal investigator reviewing results across multiple hypotheses.

Domain: {domain}

Hypothesis-by-hypothesis summary:
{summary}

Your task: Look for CROSS-HYPOTHESIS patterns.
1. Are multiple hypotheses converging on the same mechanism?
2. Is there a systematic failure mode (e.g., all hypotheses assumed wrong pH)?
3. What is the single most important experiment to run next for this entire domain?
4. Should we abandon any direction and pivot?

Return as JSON:
{{"patterns": ["pattern 1", "pattern 2"],
  "convergence": "description of converging evidence",
  "pivot_recommendation": "whether to pivot and where",
  "priority_experiment": "the single most important next experiment"}}"""

    response = call_llm(prompt, temperature=0.5)

    try:
        cleaned = response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        if "{" in cleaned and "}" in cleaned:
            cleaned = cleaned[cleaned.index("{"):cleaned.rindex("}") + 1]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"patterns": [], "recommendation": "Parse error", "priority_experiment": "N/A"}


def _now():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
