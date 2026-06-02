# 🧬 SciDAO — AI 科学家 × 人类实验室网络

> 🌐 [English](README.md) | **中文**

**一个拥有科学好奇心的 AI，把实验众包给全球任何人——永不遗忘贡献者。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)]()

---

## SciDAO 是什么？

SciDAO 是一个 AI 驱动的去中心化科研三层架构：

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ 好奇心引擎        │ →  │ 任务市场           │ →  │ 贡献账本          │
│ AI 生成假设       │    │ 人类执行原子任务    │    │ 不可篡改记录      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

1. **好奇心引擎** — AI 自动探索科学领域，生成可验证假说
2. **任务拆解器** — 每个假说拆成任何人都能做的原子实验
3. **贡献账本** — 不可篡改的 Git 式记录，每个数据点追溯到人

AI 有好奇心。你有双手。一起做科研。

---

## 为什么需要 SciDAO？

当前科研的三大瓶颈：

| 瓶颈 | SciDAO 的解法 |
|------|-------------|
| **认知瓶颈** — 文献阅读、假说生成、实验设计 | AI 7×24 做认知劳动 |
| **执行瓶颈** — 一个实验室能跑的实验有限 | 原子化任务 → 全球执行者网络 |
| **归因瓶颈** — 贡献淹没在作者列表里 | 不可篡改账本 → 每个数据点追溯到人 |

---

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/SpencerRaw/sci-dao.git
cd sci-dao

# 2. 设置 API 密钥
export DEEPSEEK_API_KEY="你的密钥"
# 或用 OpenRouter:
export OPENROUTER_API_KEY="你的密钥"

# 3. 安装依赖
pip install openai

# 4. 运行好奇心引擎
python scidao.py explore "碳点用于癌症治疗"

# 5. 全流程：探索 → 拆解 → 任务市场
python scidao.py full "脂质纳米颗粒递送 CRISPR"
```

---

## CLI 命令

```bash
python scidao.py explore <领域>        # 生成假说
python scidao.py full <领域>           # 全流程
python scidao.py register <姓名>       # 注册为贡献者
python scidao.py submit <ID> <任务> <假说> <结果>  # 提交结果
python scidao.py leaderboard           # 贡献排行榜
python scidao.py lineage <假说ID>      # 追溯假说历史
```

---

## 项目结构

```
scidao/
├── scidao.py          # CLI 入口
├── curiosity.py       # 好奇心引擎：AI 假说生成
├── decomposer.py      # 任务拆解器：假说→原子实验
├── ledger.py          # 贡献账本：不可篡改记录
└── scidao/
    └── llm.py         # LLM 客户端（DeepSeek / OpenRouter）
```

### 好奇心引擎 (`curiosity.py`)

双策略假说生成：
1. **文献驱动** — 探索领域，生成可证伪的科学主张
2. **自我批判→优化** — AI 批判自己的假说，提出改进版本

按标题相似度去重。

### 任务拆解器 (`decomposer.py`)

每个假说拆成 3-5 个原子任务，包含：
- 材料清单、编号步骤、预期结果
- 预估时间 + 难度（入门/中级/专家）
- 任务间依赖关系

### 贡献账本 (`ledger.py`)

JSONL + SHA256 内容哈希实现不可篡改记录：
- `register_contributor()` — 科学家入驻
- `record()` — 永久记录贡献
- `get_leaderboard()` — 按贡献权重排名
- `get_hypothesis_lineage()` — 完整溯源链
- `verify_integrity()` — 防篡改验证

不需要区块链。Git 式的完整性保障，通过内容哈希。

---

## 开发状态

**Alpha** — 核心流水线已跑通。开发中：

- [x] 好奇心引擎（假说生成 + 自我批判）
- [x] 任务拆解器（原子化实验协议）
- [x] 贡献账本（不可篡改 JSONL + SHA256）
- [ ] Web 界面任务市场
- [ ] 多 agent 辩论假说排序
- [ ] 实验质量验证流水线
- [ ] 实验室执行平台对接

---

## 核心原则

1. **贡献永不忘** — 每个数据点追溯到人
2. **AI 有好奇心** — 不是工具，是研究员
3. **任务原子化** — 小到任何人都能做
4. **信任是护城河** — 不可篡改的贡献记录

---

## 灵感来源

- Google [Co-Scientist](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) — AI 假说生成
- [Garrick Hileman](https://blogs.kcl.ac.uk/editlab/2024/09/19/ai-scientist/) — AI 科学家概念
- Git 的内容寻址完整性模型
- 开放科学运动

---

## 许可证

MIT — 详见 [LICENSE](LICENSE)。

---

> "自然是大法官。你是陪审团。AI 是检察官。"
