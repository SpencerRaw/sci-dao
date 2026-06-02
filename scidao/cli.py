#!/usr/bin/env python3
"""
SciDAO CLI — AI with scientific curiosity that hires humans.

Commands: explore, full, register, submit, leaderboard, lineage
"""

import json
import os

from scidao.curiosity import generate_hypotheses, explore_domain
from scidao.decomposer import decompose_hypothesis, estimate_effort
from scidao.ledger import ContributionLedger


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
    
    return hypos


def cmd_decompose(hypotheses: list[dict], domain: str):
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
    
    return all_tasks


def cmd_register(name: str, skills: list[str] = None):
    """Register a contributor."""
    ledger = ContributionLedger()
    cid = ledger.register_contributor(name, skills=skills or [])
    print(f"✅ Registered: {name} ({cid})")
    return cid


def cmd_submit(contributor_id: str, task_id: str, hypothesis_id: str, 
               result: str):
    """Submit an experiment result."""
    ledger = ContributionLedger()
    
    if contributor_id not in ledger.contributors:
        print(f"❌ Unknown contributor: {contributor_id}")
        print("   Register first: scidao register <name>")
        return
    
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
    """Show all contributions for a hypothesis."""
    ledger = ContributionLedger()
    lineage = ledger.get_hypothesis_lineage(hypothesis_id)
    
    print(f"\n📜 Hypothesis Lineage: {hypothesis_id}\n")
    for e in lineage:
        name = ledger.contributors.get(e["contributor_id"], {}).get("name", "Unknown")
        print(f"  [{e['timestamp']}] {name}")
        print(f"      {e['content_preview'][:120]}")
        print(f"      Weight: {e['weight']}  Hash: {e['content_hash'][:16]}")
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
    
    # Step 1: Curiosity
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
  4. Submit:     scidao submit <your-id> <task-id> <hypo-id> "your results"
  5. Get credit: Your contribution is permanently recorded in the ledger
  
  The AI will learn from your results and generate better hypotheses.
  Nature is the judge. You are the jury.
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
    
    # submit
    p = sub.add_parser("submit", help="Submit experiment results")
    p.add_argument("contributor_id", help="Your contributor ID")
    p.add_argument("task_id", help="Task ID")
    p.add_argument("hypothesis_id", help="Hypothesis ID")
    p.add_argument("result", help="Your results (text)")
    
    # leaderboard
    sub.add_parser("leaderboard", help="Contribution leaderboard")
    
    # lineage
    p = sub.add_parser("lineage", help="View hypothesis contribution lineage")
    p.add_argument("hypothesis_id", help="Hypothesis ID")
    
    args = parser.parse_args()
    
    if args.command == "explore":
        cmd_explore(args.domain, args.constraints)
    elif args.command == "full":
        cmd_full_run(args.domain, args.constraints)
    elif args.command == "register":
        skills = [s.strip() for s in args.skills.split(",") if s.strip()] if args.skills else None
        cmd_register(args.name, skills)
    elif args.command == "submit":
        cmd_submit(args.contributor_id, args.task_id, args.hypothesis_id, args.result)
    elif args.command == "leaderboard":
        cmd_leaderboard()
    elif args.command == "lineage":
        cmd_lineage(args.hypothesis_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
