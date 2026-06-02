# SciDAO — AI-Driven Decentralized Science

> 一个拥有科学好奇心的 AI，把实验任务众包给全球任何人，永不遗忘贡献者。

---

## 架构总览

```
┌─────────────────────────────────────────────────┐
│                  SciDAO 三层                      │
│                                                  │
│  ┌─────────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ Curiosity   │  │   Task    │  │Contribution │ │
│  │   Engine    │→ │ Marketplace│→ │   Graph     │ │
│  │ (AI假设生成) │  │ (众包执行) │  │ (贡献归因)  │ │
│  └─────────────┘  └──────────┘  └─────────────┘ │
│         ↑               ↑              ↑         │
│    Co-Scientist    3 bio clients    区块链/Git   │
│       改造           冷启动          like         │
└─────────────────────────────────────────────────┘
```

---

## Speed! 三线并行迭代

每周一个 sprint，c4/d4/e4 同时推。

---

### 🔨 c4 Build Game — 技术基建

#### Sprint 1: 好奇心 MVP
- [ ] 从 Co-Scientist 提取 HypothesisGenerator 为独立模块
- [ ] 定义「好奇心」：给定一个科学领域，自动生成 N 个可测试假设
- [ ] 第一个 domain: 碳点抗癌 (接第一个试点 client)
- [ ] 输出格式: `{hypothesis, rationale, required_experiments, confidence_score}`

#### Sprint 2: 任务拆解器
- [ ] 把「验证假设」拆成原子任务
- [ ] 每个任务 = 一个人能独立执行的最小单元
- [ ] 标准化 SOP 模板: `{materials, steps, expected_result, time_estimate, difficulty}`
- [ ] 示例: "用 50μg/ml CD-NIR 处理 HeLa 细胞 24h，MTT 测 viability，拍照"

#### Sprint 3: 贡献图谱 v0
- [ ] 纯 Git-based 贡献追踪 (先用 Git 不用区块链)
- [ ] 每个任务 = 一个 issue
- [ ] 执行者 fork → 提交结果 → PR → merge = 贡献记录
- [ ] 自动生成 contribution weight

#### Sprint 4: 匹配引擎
- [ ] 任务标签化 (domain, difficulty, equipment_needed)
- [ ] 执行者 profile (skills, equipment, past_completions)
- [ ] 简单匹配: TF-IDF + 规则
- [ ] 自动推送任务给匹配的执行者

#### Sprint 5: 知识图谱
- [ ] 实验结果 → 结构化存储
- [ ] 假设验证状态追踪 (confirmed/refuted/inconclusive)
- [ ] AI 从结果中学习，优化后续假设

---

### 📦 d4 Deliver Game — 获取用户

#### Sprint 1: 冷启动种子
- [ ] 和 seed client A 讨论: 碳点 PCD 实验拆解
- [ ] 和 seed client B 讨论: NIR 碳点园艺实验
- [ ] 记录每个教授最痛的点、现有实验瓶颈

#### Sprint 2: 第一个付费 pilot
- [ ] 选一个 client，跑一次完整的 AI 假设→众包执行→结果
- [ ] 哪怕只有一个实验、一个执行者
- [ ] 记录整个流程的时间、成本、质量

#### Sprint 3: 执行者招募
- [ ] 目标: 10 个可用的实验执行者
- [ ] 来源: 生物 freelancer 平台、大学实验员、CRO
- [ ] 触达方式: LinkedIn DM + 学术社群 + 熟人推荐
- [ ] 每日触达 5 人 (保持 d4 节奏)

#### Sprint 4: 付费模型验证
- [ ] 测试定价: per-experiment vs subscription vs outcome-based
- [ ] 收集 3 个付费意愿反馈
- [ ] 迭代定价

#### Sprint 5: 第一个 case study
- [ ] 完整的 before/after 对比
- [ ] 传统课题组 vs SciDAO 模式
- [ ] 时间、成本、质量量化

---

### 📣 e4 Promote Game — 内容与社区

#### Sprint 1: 愿景文章
- [ ] 发布第一篇文章: "AI Has Scientific Curiosity — What Happens Next?"
- [ ] 平台: 公众号 + HN + Reddit r/MachineLearning
- [ ] 阐述: AI好奇心 + 科学众包 + 贡献图谱

#### Sprint 2: 技术拆解
- [ ] 发布 Co-Scientist 复现的 88%还原度经验
- [ ] 开源 MVP 代码 (Curiosity Engine)
- [ ] GitHub repo + README

#### Sprint 3: 社区启动
- [ ] 建立 Telegram/Discord 社区
- [ ] 邀请 3 个 client + 10 个执行者
- [ ] 第一个 AMA: "科学的未来是 AI + 众包吗？"

#### Sprint 4: 案例发布
- [ ] Pilot 实验结果公开发布
- [ ] 强调贡献者 attribution
- [ ] 媒体 outreach: Nature News, The Scientist, 生物自媒体

#### Sprint 5: 融资叙事
- [ ] Deck v1: problem → solution → traction → team → ask
- [ ] YC application draft
- [ ] 接触 5 个天使投资人

---

## 不变的核心原则

1. **贡献永不忘** — 每一个数据点都追溯到人
2. **AI 有好奇心** — 不是工具，是研究员
3. **任务原子化** — 小到任何人都能做
4. **速度赢一切** — 7:2:1 分配，迭代×10-100
5. **信任是护城河** — 不可篡改的贡献记录

---

## 开放问题

- [ ] 区块链到底要不要？先 Git 跑通再评估
- [ ] 质量控制的最后防线：AI 审核 + 随机抽检 + 信誉系统？
- [ ] 知识产权归谁？贡献者共享 vs DAO 持有 vs 公共域？
- [ ] 第一个杀手级实验是什么？必须简单、可验证、有科学意义
- [ ] 中文还是英文优先？建议英文 (全球执行者) + 中文 (client 沟通)

---

## 与现有项目的关系

```
| Co-Scientist (复现)        → Curiosity Engine (AI假设生成)
| 3 seed clients             → Seed users + 实验来源
freelancer outreach (d4)  → 执行者招募
content creation (e4)     → 社区建设 + 融资叙事
100M offer                → SciDAO 的产品化版本
```

---

*Created: 2026-05-30 | Next review: after Sprint 1*
