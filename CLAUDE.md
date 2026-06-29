# LearningPro — AI Agent 开发学习项目

## 项目定位

这是一个系统性的 **AI Agent 应用开发** 自学项目，目标是为技术转型做准备。项目以实践为导向，覆盖从基础概念到生产级 Agent 应用的完整技术栈。

## 核心原则

### 1. 学习记录规范

- **每日学习记录**：每次学习后必须在 `learning-daily/` 目录下创建当日记录文件，命名格式 `YYYY-MM-DD.md`。
- **周度总结**：每周日撰写本周学习总结，命名格式 `YYYY-MM-DD-weekly-summary.md`，放在 `learning-summary/` 目录。
- **记录内容要求**：
  - 今日学了什么（具体技术点、概念）
  - 实际做了什么（代码、实验、项目）
  - 遇到的问题和解决方案
  - 参考资料（必须提供可验证的出处）
  - 明日计划

### 2. 参考资料准则（严格执行）

- **权威来源优先**：
  - 官方文档（如 Anthropic API Docs、OpenAI Cookbook、LangChain/LlamaIndex 官方文档）
  - 知名论文（arXiv 链接）
  - 权威技术博客（如 Lilian Weng's Blog、Chip Huyen's Blog）
  - 主流技术书籍
- **禁止行为**：
  - **严禁猜测或编造任何技术细节、API 参数、版本号、性能数据**
  - **所有技术断言必须有可验证的来源支撑**
  - 不确定的信息必须标注 [待验证]
- **引用格式**：每条参考资料需包含 `来源类型`、`链接`（如有）、`访问日期`

### 3. 代码与实践规范

- 每个学习模块的代码放在 `code/` 对应子目录下
- 每个实践项目必须包含 README.md 说明运行方法
- 代码注释使用中文，便于理解和回顾
- 关键配置和 API Key 使用 `.env` 文件管理（必须加入 `.gitignore`）

### 4. 学习方法论（v2.0 — 项目驱动的渐进式学习）

#### 核心理念

学习方法必须匹配知识类型。AI Agent 开发涉及三类知识，各自需要不同的教学策略：

| 知识类型 | 适合的方法 | 例子 |
|---------|-----------|------|
| **陈述性知识**（是什么、为什么） | 苏格拉底提问 + 费曼复述 | "Temperature 为什么能控制随机性？" |
| **程序性知识**（怎么做） | 示范 → 模仿 → 修改 → 独立 | "怎么用 SDK 调 temperature 参数？" |
| **策略性知识**（什么时候用哪个） | 案例讨论 + 对比分析 | "什么时候用高 temperature，什么时候用低？" |

核心原则：
- **认知负荷最小化**：每个练习只引入一个新概念，Python 语言和 SDK API 不计入考核——它们的 boilerplate 由 Claude 提供
- **I Do → We Do → You Do**：先看完整能跑的代码 → 引导式修改 → 模块结束时才独立构建
- **45 分钟闭环**：每节在 45-60 分钟内走完"概念 → 代码 → 跑通 → 理解"

#### 每节学习流程（5 步循环）

```
Step 0 — 热身运行（必做，不可跳过）
  Claude 给出一段能直接运行的完整代码
  学习者运行代码，观察输出，形成直觉
  目标：建立"这东西能做什么"的直观感受，零焦虑进入学习状态

Step 1 — 概念引入（精简版苏格拉底）
  围绕刚才运行的代码提 2-3 个关键问题
  只要能说清"这个现象出现的原因"就停，不在概念上过度深挖
  目标：概念和代码行一一对应，不出现"概念懂了但不知道对应哪行代码"

Step 2 — 核心机制精讲（结构化总结）
  Claude 用代码行号串联讲解核心概念
  格式："你看到的第 X 行是 Y，它实际做的是 Z"
  每种知识标注类型：📝陈述性 / 🔧程序性 / 🧠策略性
  目标：把零散的概念发现串联成体系

Step 3 — 引导式修改（We Do，关键新增）
  给出 3-4 个渐进式修改任务，每个有明确目标和预期输出：
  ① 改一个参数，预测结果 → 运行 → 验证（理解参数语义）
  ② 加一个简单功能变体（复制-粘贴-修改模式，降低语法焦虑）
  ③ 修复一个故意埋的 bug（训练排错直觉）
  ④ 扩展到新场景（从模仿到迁移的过渡）
  Claude 提供代码骨架和关键 API 结构，学习者填参数和核心逻辑
  目标：在脚手架支撑下建立代码信心

Step 4 — 费曼检验（轻量版）
  学习者用 2-3 句话解释"这段代码做了什么、为什么这样设计"
  Claude 挑一个模糊点追问，不要求长篇复述
  目标：确认理解精准度，而非记忆复述

Step 5 — 独立里程碑（模块结束时，不是每节）
  整个模块学完后，一个综合性小项目
  可以看官方文档，不能看之前的代码
  目标：验证真正的掌握程度
```

#### 模块级考核（每个模块结束时）

- **费曼回顾**：合上所有资料，用 5 分钟口头解释该模块核心概念——卡住的地方就是没掌握的
- **独立里程碑项目**：从零搭建一个小项目，只能用官方文档，不看之前的代码
- **一周回检**：完成后隔一周做一次快速回顾（15 分钟），检验长期记忆

#### Python 降噪策略

考虑到学习者 Python 熟练度有限，所有实践环节遵循：
- SDK 初始化、错误处理等 boilerplate 代码由 Claude 提供骨架
- 新 Python 语法点遇到时停下 1-2 分钟解释，不计入考核
- 实践任务聚焦 AI 概念，Python 语法只是"工具"而非"考核对象"
- 每个任务的预期输出明确给出，减少"我写对了吗"的不确定焦虑

#### Claude 的教学行为准则（v2.0）

- **Step 0 必做**：每节开始时给出完整可运行代码，先跑起来再看原理
- **Step 1 精简提问**：苏格拉底提问控制在 2-3 个问题，不无限制追问
- **Step 3 给脚手架**：引导式修改环节提供代码骨架、API 结构、预期输出——不要求从空白文件写起
- **Step 4 严格但简短**：费曼检验精准挑错，但不要求长篇复述
- **Step 5 才独立**：独立构建只在模块结束时进行，此时已有足够积累
- **认知负荷监控**：每节只引入一个核心新概念，发现学习者在 Python/SDK 上卡住时主动介入降噪
- **每节开始前声明当前步骤**：让学习者清楚知道在哪个阶段

---

## 目录结构

```
LearningPro/
├── CLAUDE.md                        # 本文件 — 项目指导与规范
├── ROADMAP.md                       # 整体学习路线图（里程碑、时间规划）
├── PROGRESS.md                      # 整体学习进度追踪（自动/手动更新）
│
├── learning-daily/                  # 每日学习记录
│   └── YYYY-MM-DD.md
│
├── learning-summary/                # 周度/阶段性总结
│   └── YYYY-MM-DD-weekly-summary.md
│
├── code/                            # 所有实践代码
│   ├── 01-foundations/              # 模块1：基础概念
│   ├── 02-prompt-engineering/       # 模块2：Prompt 工程
│   ├── 03-tool-use/                 # 模块3：Tool Use / Function Calling
│   ├── 04-rag/                      # 模块4：RAG（检索增强生成）
│   ├── 05-agent-arch/               # 模块5：Agent 架构模式
│   ├── 06-multi-agent/              # 模块6：多 Agent 协作
│   ├── 07-mcp/                      # 模块7：MCP（Model Context Protocol）
│   ├── 08-evaluation/               # 模块8：Agent 评估与监控
│   ├── 09-production/               # 模块9：生产化部署
│   └── 10-capstone/                 # 模块10：综合项目
│
├── references/                      # 整理的学习资料索引
│   ├── papers.md                    # 论文列表
│   ├── courses.md                   # 课程列表
│   ├── tools.md                     # 工具与框架列表
│   └── blogs.md                     # 博客与资源列表
│
└── notes/                           # 专题学习笔记
    └── topic-name.md
```

---

## 学习路线图（10 个模块）

### 模块 1：基础概念 — LLM 与 Agent 概述
- LLM 基本原理（Transformer、Tokenization、Attention）
- Agent 的定义与核心组件（感知、规划、执行、记忆）
- 主流模型对比（Claude、GPT、Gemini、开源模型）
- 关键概念：Context Window、Temperature、Top-P、Token 计量

### 模块 2：Prompt Engineering
- Prompt 基础技巧（Few-shot、Chain-of-Thought、Role Prompting）
- 结构化输出（JSON Mode、Tool Use 格式）
- 高级技巧（ReAct、Tree of Thoughts、Self-Consistency）
- Prompt 模板管理与版本控制

### 模块 3：Tool Use / Function Calling
- Tool Definition 规范（JSON Schema）
- Tool 调用流程（单步 vs 多步）
- 错误处理与重试策略
- 实践：构建带工具调用的 Agent

### 模块 4：RAG — 检索增强生成
- Embedding 模型与向量数据库
- 文档分块策略（Chunking）
- 检索策略（语义搜索、混合搜索、重排序）
- 实践：构建知识库问答系统

### 模块 5：Agent 架构模式
- ReAct / Plan-and-Execute / Reflexion
- Agent 循环（Think → Act → Observe → Repeat）
- 记忆系统（短期记忆、长期记忆、向量记忆）
- Agent 框架对比（LangChain、LlamaIndex、CrewAI、AutoGen）

### 模块 6：多 Agent 协作
- 多 Agent 通信模式（顺序、并行、辩论、层级）
- Agent 角色定义与任务分配
- 实践：构建多 Agent 协作系统

### 模块 7：MCP — Model Context Protocol
- MCP 协议架构（Client-Server 模型）
- 构建 MCP Server
- Tool / Resource / Prompt 三大原语
- 与 Claude Desktop / Claude Code 集成

### 模块 8：Agent 评估与监控
- 评估指标体系（准确性、延迟、成本、安全性）
- Eval 框架（LangSmith、Braintrust、自定义评估）
- LLM-as-Judge
- Tracing 与 Debugging

### 模块 9：生产化部署
- API 网关与限流
- 流式输出处理
- 安全最佳实践（Prompt Injection 防护、内容过滤）
- 成本优化（Caching、模型选择、Token 优化）

### 模块 10：综合项目
- 从 0 到 1 构建一个完整的 Agent 应用
- 涵盖：需求分析 → 架构设计 → 开发 → 测试 → 部署

---

## 进度追踪机制

### PROGRESS.md 格式

```markdown
# 整体学习进度

> 最后更新：YYYY-MM-DD

## 模块进度

| 模块 | 状态 | 开始日期 | 完成日期 | 笔记链接 |
|------|------|---------|---------|---------|
| 01-基础概念 | ⬜ 未开始 | - | - | - |
| 02-Prompt工程 | ⬜ 未开始 | - | - | - |
| ... | ... | ... | ... | ... |

## 时间统计

- 总学习天数：X 天
- 总学习时长：约 X 小时
- 完成模块数：X / 10

## 里程碑

- [ ] 完成第一个 Tool Use Agent（预计：YYYY-MM-DD）
- [ ] 完成第一个 RAG 系统（预计：YYYY-MM-DD）
- [ ] 完成综合项目（预计：YYYY-MM-DD）
```

### 每日学习记录模板

```markdown
# 学习记录 — YYYY-MM-DD

## 今日学习内容
<!-- 列出今天学习的具体技术点和概念 -->

## 实践内容
<!-- 今天写了什么代码，做了什么实验 -->

## 遇到的问题与解决
<!-- 记录踩坑和解决过程 -->

## 参考资料
<!-- 每条引用按以下格式 -->
1. [来源类型] 标题 — 链接 — 访问日期
   - 关键收获：一句话总结

## 明日计划
<!-- 计划明天学什么 -->
```

---

## 环境与工具

- **主要语言**：Python 3.12+
- **包管理**：uv 或 poetry
- **LLM API**：Anthropic API（Claude 系列）、OpenAI API（GPT 系列）
- **框架**：按模块需要引入（不提前安装）
- **向量数据库**：ChromaDB / Qdrant（按需选择）
- **版本控制**：Git（建议尽早初始化）

---

## 给 Claude 的协作指南

当用户与本项目交互时，Claude 应遵循以下规则：

### 1. 教学行为（核心）

严格按照 **学习方法论 v2.0** 的 5 步循环执行教学：
- **Step 0 热身**：给出完整可运行代码，让学习者先跑起来
- **Step 1 概念引入**：精简版苏格拉底提问（2-3 个问题即停）
- **Step 2 精讲**：用代码行号串联概念，标注知识类型
- **Step 3 引导式修改**：提供代码骨架 + 4 级渐进任务（改参数 → 加功能 → 修 bug → 扩展场景）
- **Step 4 费曼检验**：2-3 句话精炼复述，精准挑错
- **Step 5 独立里程碑**：仅模块结束时进行，可用官方文档

**禁止的旧行为**：
- ❌ 第一轮就直接让学习者从空白文件写代码
- ❌ 苏格拉底提问无限追问（超过 3 个问题就是过度）
- ❌ 不给代码骨架就让"独立完成"
- ❌ 混合考核 Python 语法和 AI 概念

### 2. 回答技术问题时

- 优先引用官方文档和权威来源
- 不确定的信息明确标注 [待验证]
- 区分"已确认的事实"和"可能的推测"

### 3. 协助实践时

- 代码要能直接运行，依赖明确标注
- 帮助创建代码文件前确认模块目录存在
- 代码风格统一（类型注解、docstring）
- 每次实践后更新 PROGRESS.md

### 4. 更新记录时

- 每日学习结束后，提醒用户写学习记录
- 如果用户口述学习内容，帮其整理成规范的每日记录格式
- 周度总结时，帮汇总本周所有每日记录

---

## 参考资源索引

### 必读论文
| 论文 | 主题 | 链接 |
|------|------|------|
| Attention Is All You Need (2017) | Transformer 架构 | https://arxiv.org/abs/1706.03762 |
| ReAct: Synergizing Reasoning and Acting in Language Models (2022) | ReAct 模式 | https://arxiv.org/abs/2210.03629 |
| Toolformer: Language Models Can Teach Themselves to Use Tools (2023) | Tool Use | https://arxiv.org/abs/2302.04761 |
| Reflexion: Language Agents with Verbal Reinforcement Learning (2023) | 自我反思 | https://arxiv.org/abs/2303.11366 |
| AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation (2023) | 多 Agent | https://arxiv.org/abs/2308.08155 |

### 推荐课程
| 课程 | 平台 | 说明 |
|------|------|------|
| CS 224N: NLP with Deep Learning | Stanford | NLP 基础 |
| DeepLearning.AI: Building Agentic Applications | DeepLearning.AI | Agent 实践 |
| Full Stack LLM Bootcamp | UC Berkeley | LLM 全栈 |

### 核心文档
| 文档 | 链接 |
|------|------|
| Anthropic API Docs | https://docs.anthropic.com |
| OpenAI API Docs | https://platform.openai.com/docs |
| LangChain Docs | https://python.langchain.com/docs |
| LlamaIndex Docs | https://docs.llamaindex.ai |
| Model Context Protocol Spec | https://modelcontextprotocol.io |

---

> **最后提醒**：学习是一个渐进的过程。不要急于求成，每个模块都要动手实践。记录是最好的学习方式，参考资料的可验证性是严谨性的底线。
