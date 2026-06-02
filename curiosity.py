"""
Curiosity Engine v0 — AI with scientific curiosity.
Given a research domain, generates testable hypotheses.
Uses the standalone scidao.llm client.
"""

import json
from scidao.llm import call_llm


def generate_hypotheses(domain: str, constraints: str = "", num: int = 5) -> list[dict]:
    """
    Curiosity Engine: let AI explore a domain and generate hypotheses.

    Args:
        domain: Research domain description (e.g. "carbon dot cancer therapy")
        constraints: Optional constraints (e.g. "must be testable in vitro")
        num: Number of hypotheses to generate

    Returns:
        List of dicts with title, text, rationale, novelty_score
    """
    # Strategy 1: Literature-grounded generation
    prompt_lit = f"""You are an AI scientist with genuine scientific curiosity.
    
Research Domain: {domain}
{constraints if constraints else ''}

Your task: Explore this domain and generate {num} novel, testable hypotheses.
For each hypothesis:
- Propose a specific, falsifiable claim
- Explain the rationale (why this might be true)
- Suggest how it could be tested

Think creatively. Explore unconventional angles and interdisciplinary connections.
Each hypothesis must be specific and testable — not vague research directions.

Return as JSON array:
[{{"title": "...", "text": "...", "rationale": "...", "testability": "HIGH|MEDIUM|LOW"}}]"""

    raw = call_llm(prompt_lit, temperature=0.8)
    
    # Parse
    try:
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        if "[" in cleaned:
            cleaned = cleaned[cleaned.index("["):cleaned.rindex("]")+1]
        hypotheses = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: try to extract line by line
        hypotheses = [{"title": "Parse Error", "text": raw[:500], 
                       "rationale": "Failed to parse LLM output", "testability": "UNKNOWN"}]
    
    # Strategy 2: Self-critique → refine
    if len(hypotheses) >= 2:
        critique_prompt = f"""Domain: {domain}

You generated these hypotheses:
{json.dumps(hypotheses, indent=2)}

Now CRITIQUE your own work. For each hypothesis:
1. What assumption might be wrong?
2. What alternative explanation is possible?
3. Is this truly novel or a rephrase of known work?

Then propose 2 improved hypotheses that address your critiques.
Return as JSON array: [{{"title": "...", "text": "...", "rationale": "...", 
                        "testability": "HIGH|MEDIUM|LOW", "improved_from": "original critique"}}]"""

        refined_raw = call_llm(critique_prompt, temperature=0.7)
        try:
            cleaned = refined_raw.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            if "[" in cleaned:
                cleaned = cleaned[cleaned.index("["):cleaned.rindex("]")+1]
            refined = json.loads(cleaned)
            hypotheses.extend(refined)
        except json.JSONDecodeError:
            pass  # Keep original
    
    # Deduplicate by title similarity
    seen = set()
    unique = []
    for h in hypotheses:
        title_key = h.get("title", "")[:50].lower().strip()
        if title_key and title_key not in seen:
            seen.add(title_key)
            # Add ID
            h["id"] = f"HYP-{len(seen):03d}"
            unique.append(h)
    
    return unique


def explore_domain(domain: str, iterations: int = 1) -> list[dict]:
    """
    Multi-iteration exploration: AI refines its curiosity across rounds.
    Each iteration feeds previous results back to the AI.
    """
    all_hypotheses = []
    previous_best = ""
    
    for i in range(iterations):
        if previous_best:
            prompt = f"""Domain: {domain}

Previous round's best finding: {previous_best}

Now dig DEEPER. What question does this finding raise? 
What adjacent territory should we explore?
Generate 3 new hypotheses that build on or challenge the previous finding.

Return JSON array same format as before."""
            result = generate_hypotheses(domain, prompt, num=3)
        else:
            result = generate_hypotheses(domain, num=5)
        
        all_hypotheses.extend(result)
        
        if result:
            previous_best = f"{result[0].get('title')}: {result[0].get('text', '')[:200]}"
    
    return all_hypotheses


if __name__ == "__main__":
    # Quick test
    domain = "carbon dots for near-infrared light-regulated plant growth"
    hypos = generate_hypotheses(domain, num=3)
    print(json.dumps(hypos, indent=2, ensure_ascii=False))
