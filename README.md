# 🧬 SciDAO — AI Scientist × Human Lab Network

> 🌐 **English** | [中文文档](README.zh-CN.md)

**An AI with scientific curiosity that distributes experiments to humans — with immutable contribution tracking.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)]()

---

## What is SciDAO?

SciDAO is a three-layer architecture for AI-driven decentralized science:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Curiosity Engine │ →  │  Task Marketplace │ →  │Contribution Ledger│
│ AI generates     │    │  Humans execute   │    │  Immutable record │
│ hypotheses       │    │  atomized tasks   │    │  of every datapoint│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

1. **Curiosity Engine** — AI explores a scientific domain and generates testable hypotheses
2. **Task Decomposer** — Each hypothesis becomes atomized experiments anyone can run
3. **Contribution Ledger** — Immutable, Git-like record of who did what

The AI has curiosity. You have hands. Let's do science together.

---

## Why SciDAO?

Three bottlenecks in current research:

| Bottleneck | SciDAO's Solution |
|------------|-------------------|
| **Cognitive** — literature, hypotheses, experimental design | AI does cognitive labor 24/7 |
| **Execution** — one lab can only run so many experiments | Atomized tasks → global executor network |
| **Attribution** — contributions buried in author lists | Immutable ledger → every datapoint traced to a person |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/SpencerRaw/sci-dao.git
cd sci-dao

# 2. Set API key
export DEEPSEEK_API_KEY=sk-...  # or use OpenRouter:
export OPENROUTER_API_KEY=sk-...

# 3. Install dependencies
pip install openai

# 4. Run the curiosity engine
python scidao.py explore "carbon dots for cancer therapy"

# 5. Full pipeline: explore → decompose → marketplace
python scidao.py full "lipid nanoparticles for CRISPR delivery"
```

---

## CLI Commands

```bash
python scidao.py explore <domain>         # Generate hypotheses
python scidao.py full <domain>            # Full pipeline
python scidao.py register <name>          # Register as a contributor
python scidao.py submit <id> <task> <hypothesis> <result>  # Submit results
python scidao.py leaderboard              # Contribution rankings
python scidao.py lineage <hypothesis-id>  # Trace hypothesis history
```

---

## Architecture

```
scidao/
├── scidao.py          # CLI entry point
├── curiosity.py       # Curiosity Engine: AI hypothesis generation
├── decomposer.py      # Task Decomposer: hypothesis → atomized experiments
├── ledger.py          # Contribution Ledger: immutable records
└── scidao/
    └── llm.py         # LLM client (DeepSeek / OpenRouter)
```

### Curiosity Engine (`curiosity.py`)

Dual-strategy hypothesis generation:
1. **Literature-grounded** — explore a domain, generate falsifiable claims
2. **Self-critique → refinement** — AI critiques its own hypotheses, proposes improvements

Deduplication by title similarity.

### Task Decomposer (`decomposer.py`)

Each hypothesis becomes 3-5 atomized tasks with:
- Materials list, numbered protocol steps, expected results
- Time estimate + difficulty (BEGINNER / INTERMEDIATE / EXPERT)
- Inter-task dependencies

### Contribution Ledger (`ledger.py`)

JSONL + SHA256 content hashing for immutable records:
- `register_contributor()` — onboard a scientist
- `record()` — permanently record a contribution
- `get_leaderboard()` — rank contributors by weight
- `get_hypothesis_lineage()` — full provenance chain
- `verify_integrity()` — tamper-proof verification

No blockchain needed. Git-style integrity via content hashing.

---

## Development Status

**Alpha** — core pipeline functional. In development:

- [x] Curiosity Engine (hypothesis generation + self-critique)
- [x] Task Decomposer (atomized experiment protocols)
- [x] Contribution Ledger (immutable JSONL + SHA256)
- [ ] Web interface for task marketplace
- [ ] Multi-agent debate ranking of hypotheses
- [ ] Experiment quality verification pipeline
- [ ] Lab execution platform integrations

---

## Core Principles

1. **Contributions Never Forgotten** — every datapoint traces to a person
2. **AI Has Curiosity** — not a tool, a researcher
3. **Tasks Atomized** — small enough for anyone to execute
4. **Trust Is the Moat** — immutable contribution records

---

## Inspiration

- Google's [AI Co-Scientist](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) — AI hypothesis generation
- [AI Scientist](https://blogs.kcl.ac.uk/editlab/2024/09/19/ai-scientist/) concept by Garrick Hileman
- Git's content-addressable integrity model
- The open science movement

---

## License

MIT — see [LICENSE](LICENSE).

---

> "Nature is the judge. You are the jury. The AI is the prosecutor."

## Contributing

Issues and PRs welcome. Before submitting:

```bash
pip install -e "."
pytest
```

See [PLAN.md](PLAN.md) for roadmap and design decisions.
