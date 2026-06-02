#!/usr/bin/env python3
"""
SciDAO CLI — AI with scientific curiosity that hires humans.

Commands: explore, full, register, submit, refine, analyze, leaderboard, lineage
"""

import json
import os

from scidao.curiosity import generate_hypotheses, explore_domain
from scidao.decomposer import decompose_hypothesis, estimate_effort
from scidao.ledger import ContributionLedger
from scidao.learner import refine_hypothesis, analyze_across_hypotheses


SPEED_BANNER = """
╔══════════════════════════════════════════════════════╗
║  🧬 SciDAO v0 — AI Scientist × Human Lab Network   ║
║  "The AI has curiosity. You have hands."            ║
╚══════════════════════════════════════════════════════╝
"""


def cmd_explore(domain: str, constraints: str = ""):
    """Curiosity Engine: generate hypotheses for a domain."""
    print(f"\n🔬 Exploring: {domain}\n")
    
    hypos = generate_hypotheses(domain, constraints, num=5)
    
    print(f"📋 Generated {len(hypos)} hypotheses:\n")
    for i, h in enumerate(hypos, 1):
        print(f"  [{h.get('id', '?')}] {h.get('title', 'Untitled')}")
        print(f"      Testability: {h.get('testability', '?')}")
        print(f"      {h.get('text', '')[:150]}...")
        print()

    # Store hypotheses in ledger so we can retrieve them later for refinement
    ledger = ContributionLedger()
    ledger.store_hypotheses(hypos, domain)
    
    return hypos


def cmd_decompose(hypotheses: list, domain: str):
    """Task Decomposer: break hypotheses into atomized tasks."""
    all_tasks = []
    
    print("🔧 Decomposing into atomized tasks...\n")
    
    for h in hypotheses:
        tasks = decompose_hypothesis(h, domain)
        all_tasks.extend(tasks)
        
        effort = estimate_effort(tasks)
        print(f"  [{h.get('id')}] {h.get('title', '?')[:60]}")
        print(f"      → {len(tasks)} tasks, ~{effort['total_hours']}h total")
        for t in tasks:
            print(f"        [{t['id']}] {t.get('difficulty', '?')}: {t.get('title', '?')}")
        print()

    # Store tasks in ledger for lifecycle tracking
    ledger = ContributionLedger()
    ledger.store_tasks(all_tasks)
    
    return all_tasks


def cmd_register(name: str, skills: list = None):
    """Register a contributor."""
    ledger = ContributionLedger()
    cid = ledger.register_contributor(name, skills=skills or [])
    print(f"✅ Registered: {name} ({cid})")
    return cid


def cmd_submit(contributor_id: str, task_id: str, hypothesis_id: str, 
               result: str, domain: str = ""):
    """Submit an experiment result — AI learns from it."""
    ledger = ContributionLedger()
    
    if contributor_id not in ledger.contributors:
        print(f"❌ Unknown contributor: {contributor_id}")
        print("   Register first: scidao register <name>")
        return
    
    # Record the contribution
    entry_id = ledger.record(
        contributor_id=contributor_id,
        task_id=task_id,
        hypothesis_id=hypothesis_id,
        content=result,
        data_type="RAW_DATA",
        weight=0.15
    )
    
    print(f"✅ Contribution recorded: {entry_id}")
    print(f"   Content hash: {entry_id.split('-')[1]}")
    
    # ── FEEDBACK LOOP: AI learns from this result ──
    hypothesis = ledger.get_hypothesis(hypothesis_id)
    if hypothesis and domain:
        print(f"\n🧠 AI is learning from your result...\n")
        previous = ledger.get_hypothesis_lineage(hypothesis_id)
        previous_results = [e for e in previous if e.get("data_type") == "RAW_DATA"]
        
        refined = refine_hypothesis(hypothesis, result, domain, previous_results)
        
        verdict_icon = {"SUPPORTS": "✅", "REFUTES": "❌", "INCONCLUSIVE": "❓"}
        icon = verdict_icon.get(refined.get("verdict", ""), "➡️")
        
        print(f"  {icon} Verdict: {refined.get('verdict')}")
        print(f"  📊 Confidence: {refined.get('confidence', '?')}")
        print(f"  💡 Learning: {refined.get('learning', '')}")
        print(f"  🔬 Next step: {refined.get('next_step', '')}")
        
        # Save the refined hypothesis back
        ledger.store_refinement(hypothesis_id, refined)
        print(f"\n  📝 Refined hypothesis saved as {hypothesis_id}-v{ledger.get_refinement_count(hypothesis_id)}")
    elif not domain:
        print("\n  ⓘ  Tip: add --domain to enable AI learning from your result")


def cmd_refine(hypothesis_id: str, result: str, domain: str):
    """Manually refine a hypothesis with new data."""
    ledger = ContributionLedger()
    hypothesis = ledger.get_hypothesis(hypothesis_id)
    
    if not hypothesis:
        print(f"❌ Hypothesis not found: {hypothesis_id}")
        print("   Store hypotheses first: scidao explore <domain>")
        return
    
    print(f"\n🧠 Refining: {hypothesis.get('title', '?')[:80]}...\n")
    
    previous = ledger.get_hypothesis_lineage(hypothesis_id)
    previous_results = [e for e in previous if e.get("data_type") == "RAW_DATA"]
    
    refined = refine_hypothesis(hypothesis, result, domain, previous_results)
    
    verdict_icon = {"SUPPORTS": "✅", "REFUTES": "❌", "INCONCLUSIVE": "❓"}
    icon = verdict_icon.get(refined.get("verdict", ""), "➡️")
    
    print(f"  {icon} Verdict: {refined.get('verdict')}")
    print(f"  📊 Confidence: {refined.get('confidence', '?')}")
    print(f"\n  📝 Refined hypothesis:")
    print(f"     {refined.get('refined_title', '')}")
    print(f"\n  💡 Learning: {refined.get('learning', '')}")
    print(f"  🔬 Next step: {refined.get('next_step', '')}")
    
    ledger.store_refinement(hypothesis_id, refined)
    v = ledger.get_refinement_count(hypothesis_id)
    print(f"\n  ✅ Saved as {hypothesis_id}-v{v}")


def cmd_analyze(domain: str):
    """Analyze patterns across all refined hypotheses in a domain."""
    ledger = ContributionLedger()
    refinements = ledger.get_all_refinements()
    
    if len(refinements) < 2:
        print(f"⚠️  Need at least 2 refined hypotheses (found {len(refinements)}).")
        print("   Submit results first: scidao submit ...")
        return
    
    print(f"\n🔍 Analyzing {len(refinements)} refinements across domain: {domain}\n")
    print("   (AI is looking for cross-hypothesis patterns...)\n")
    
    analysis = analyze_across_hypotheses(refinements, domain)
    
    patterns = analysis.get("patterns", [])
    if patterns:
        print("📊 Patterns detected:")
        for p in patterns:
            print(f"   • {p}")
    
    convergence = analysis.get("convergence", "")
    if convergence:
        print(f"\n🎯 Convergence: {convergence}")
    
    pivot = analysis.get("pivot_recommendation", "")
    if pivot:
        print(f"\n🔄 Pivot recommendation: {pivot}")
    
    priority = analysis.get("priority_experiment", "")
    if priority:
        print(f"\n⭐ Priority next experiment: {priority}")


def cmd_leaderboard():
    """Show contribution leaderboard."""
    ledger = ContributionLedger()
    board = ledger.get_leaderboard()
    
    print("\n🏆 Contribution Leaderboard\n")
    for i, c in enumerate(board, 1):
        bar = "█" * min(int(c["weight"] * 50), 50)
        print(f"  {i}. {c['name']:20s} {c['weight']:.3f}  {bar}")
        print(f"     {c['contributions']} contributions")
        print()


def cmd_lineage(hypothesis_id: str):
    """Show all contributions and refinements for a hypothesis."""
    ledger = ContributionLedger()
    lineage = ledger.get_hypothesis_lineage(hypothesis_id)
    
    print(f"\n📜 Hypothesis Lineage: {hypothesis_id}\n")
    
    # Show original hypothesis
    h = ledger.get_hypothesis(hypothesis_id)
    if h:
        print(f"  🧠 Original: {h.get('title', '?')[:100]}")
        print()
    
    # Show refinements
    refinements = ledger.get_refinements_for(hypothesis_id)
    for r in refinements:
        icon = {"SUPPORTS": "✅", "REFUTES": "❌", "INCONCLUSIVE": "❓"}.get(r.get("verdict", ""), "➡️")
        print(f"  {icon} v{r.get('version', '?')} [{r.get('verdict')}] confidence: {r.get('confidence', '?')}")
        print(f"     Learning: {r.get('learning', '')[:120]}")
        print(f"     Next: {r.get('next_step', '')[:120]}")
        print()
    
    # Show contributions
    print("  📊 Contributions:")
    for e in lineage:
        name = ledger.contributors.get(e["contributor_id"], {}).get("name", "Unknown")
        print(f"     [{e['timestamp']}] {name}: {e['content_preview'][:80]}...")
        print()


def cmd_full_run(domain: str, constraints: str = ""):
    """
    Full SciDAO pipeline:
    1. AI explores domain → generates hypotheses
    2. AI decomposes each hypothesis into atomized tasks
    3. Shows task marketplace
    4. Shows how to contribute
    """
    print(SPEED_BANNER)
    
    # Step 1: Curiosity (hypotheses auto-stored in ledger)
    hypos = cmd_explore(domain, constraints)
    
    # Step 2: Decompose
    tasks = cmd_decompose(hypos, domain)
    
    # Step 3: Marketplace summary
    print("─" * 60)
    print("📊 TASK MARKETPLACE")
    print("─" * 60)
    
    for t in tasks:
        status_icon = {"OPEN": "🟢", "CLAIMED": "🟡", "COMPLETED": "🔵", "VERIFIED": "✅"}
        icon = status_icon.get(t.get("status", "OPEN"), "⚪")
        
        print(f"{icon} [{t['id']}] {t.get('title', '?')}")
        print(f"      Difficulty: {t.get('difficulty', '?')}  "
              f"Est. time: {t.get('time_estimate', '?')}h")
        if t.get("materials"):
            print(f"      Materials: {', '.join(t['materials'][:4])}")
        print(f"      Steps: {len(t.get('steps', []))} steps")
        print()
    
    # Step 4: How to contribute
    print("─" * 60)
    print("🤝 HOW TO CONTRIBUTE")
    print("─" * 60)
    print("""
  1. Register:  scidao register "Your Name" --skills "cell culture,MTT"
  2. Claim task: Pick any OPEN task above
  3. Run experiment following the steps
  4. Submit:     scidao submit <your-id> <task-id> <hypo-id> "your results" --domain "..."
  5. AI learns:  Your result refines the hypothesis. Confidence updates.
  
  The AI learns from every result. Nature is the judge. You are the jury.
""")
    
    # Save to file
    output = {
        "domain": domain,
        "hypotheses": hypos,
        "tasks": tasks,
        "stats": {
            "total_hypotheses": len(hypos),
            "total_tasks": len(tasks),
            "open_tasks": len([t for t in tasks if t["status"] == "OPEN"])
        }
    }
    
    outpath = "output/marketplace.json"
    os.makedirs("output", exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"📁 Saved to {outpath}")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SciDAO — AI Scientist with Human Lab Network",
        prog="scidao"
    )
    sub = parser.add_subparsers(dest="command")
    
    # explore
    p = sub.add_parser("explore", help="Generate hypotheses for a domain")
    p.add_argument("domain", help="Research domain")
    p.add_argument("--constraints", default="", help="Research constraints")
    
    # full
    p = sub.add_parser("full", help="Full pipeline: explore → decompose → marketplace")
    p.add_argument("domain", help="Research domain")
    p.add_argument("--constraints", default="", help="Research constraints")
    
    # register
    p = sub.add_parser("register", help="Register as a contributor")
    p.add_argument("name", help="Your name")
    p.add_argument("--skills", default="", help="Comma-separated skills")
    
    # submit (with learning)
    p = sub.add_parser("submit", help="Submit experiment results — AI learns from them")
    p.add_argument("contributor_id", help="Your contributor ID")
    p.add_argument("task_id", help="Task ID")
    p.add_argument("hypothesis_id", help="Hypothesis ID")
    p.add_argument("result", help="Your results (text)")
    p.add_argument("--domain", default="", help="Research domain (enables AI learning)")
    
    # refine
    p = sub.add_parser("refine", help="Manually refine a hypothesis with new data")
    p.add_argument("hypothesis_id", help="Hypothesis ID to refine")
    p.add_argument("result", help="Experimental result (text)")
    p.add_argument("domain", help="Research domain")
    
    # analyze
    p = sub.add_parser("analyze", help="Cross-hypothesis pattern analysis")
    p.add_argument("domain", help="Research domain")
    
    # leaderboard
    sub.add_parser("leaderboard", help="Contribution leaderboard")
    
    # lineage (now with refinements)
    p = sub.add_parser("lineage", help="View hypothesis lineage + refinements")
    p.add_argument("hypothesis_id", help="Hypothesis ID")

    # serve
    p = sub.add_parser("serve", help="Start SciDAO REST API server")
    p.add_argument("--host", default="0.0.0.0", help="Host to bind")
    p.add_argument("--port", type=int, default=8000, help="Port to bind")

    # claim
    p = sub.add_parser("claim", help="Claim an OPEN task (48h lock)")
    p.add_argument("task_id", help="Task ID")
    p.add_argument("contributor_id", help="Your contributor ID")

    # verify
    p = sub.add_parser("verify", help="Verify a submitted task")
    p.add_argument("task_id", help="Task ID")
    
    args = parser.parse_args()
    
    if args.command == "explore":
        cmd_explore(args.domain, args.constraints)
    elif args.command == "full":
        cmd_full_run(args.domain, args.constraints)
    elif args.command == "register":
        skills = [s.strip() for s in args.skills.split(",") if s.strip()] if args.skills else None
        cmd_register(args.name, skills)
    elif args.command == "submit":
        cmd_submit(args.contributor_id, args.task_id, args.hypothesis_id, args.result, args.domain)
    elif args.command == "refine":
        cmd_refine(args.hypothesis_id, args.result, args.domain)
    elif args.command == "analyze":
        cmd_analyze(args.domain)
    elif args.command == "leaderboard":
        cmd_leaderboard()
    elif args.command == "lineage":
        cmd_lineage(args.hypothesis_id)
    elif args.command == "serve":
        from scidao.server import serve
        serve(args.host, args.port)
    elif args.command == "claim":
        ledger = ContributionLedger()
        try:
            result = ledger.claim_task(args.task_id, args.contributor_id)
            print(f"✅ Claimed: {args.task_id}")
            print(f"   Assignee: {result['assignee']}")
            print(f"   Expires: {result['expires']} (48h)")
        except ValueError as e:
            print(f"❌ {e}")
    elif args.command == "verify":
        ledger = ContributionLedger()
        try:
            result = ledger.verify_task(args.task_id)
            print(f"✅ Verified: {args.task_id}")
        except ValueError as e:
            print(f"❌ {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
