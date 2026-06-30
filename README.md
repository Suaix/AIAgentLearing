# LearningPro — AI Agent 应用开发自学项目

[![模块进度](https://img.shields.io/badge/模块进度-1%2F10-blue)](PROGRESS.md)
[![学习方法论](https://img.shields.io/badge/方法论-v2.0-green)](CLAUDE.md)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB)](https://www.python.org/)
[![包管理](https://img.shields.io/badge/pkg-uv-FFC107)](https://docs.astral.sh/uv/)

一个系统性的 **AI Agent 应用开发** 自学项目，目标是为技术转型做准备。项目以实践为导向，覆盖从基础概念到生产级 Agent 应用的完整技术栈。

---

## 📖 项目概览

这是一个 **10 模块、10-14 周**的学习路线图，从 LLM 基本原理到完整的 Agent 应用构建：

```
基础概念 → Prompt 工程 → Tool Use → RAG → Agent 架构
    → 多 Agent 协作 → MCP → 评估监控 → 生产化 → 综合项目
```

### 核心理念

- **渐进式学习**：I Do → We Do → You Do，在脚手架支撑下逐步建立代码信心
- **45 分钟闭环**：每节 45-60 分钟内走完"概念 → 代码 → 跑通 → 理解"
- **认知负荷最小化**：每个练习只引入一个新概念，Python/SDK 不计入考核
- **记录驱动**：每日记录、专题笔记、量化评估，确保学习可追溯

> 详细方法论见 [CLAUDE.md](CLAUDE.md)（项目指导规范）。

---

## 🚀 快速开始

### 环境要求

- Python 3.12+（通过 [uv](https://docs.astral.sh/uv/) 管理依赖）
- LLM API Key（支持 Anthropic / OpenAI / DeepSeek 等兼容接口）

### 安装

```bash
git clone <repo-url> && cd AIAgentLearing
uv sync
cp .env.example .env   # 编辑 .env 填入你的 API Key
```

### 运行示例

```bash
uv run python main.py                                    # 验证环境
uv run python code/01-foundations/temperature/temperature_demo.py   # 模块1示例
```

---

## 📁 项目结构

```
├── README.md                 # 本文件 — 项目首页
├── CLAUDE.md                 # Claude 协作规范 + 学习方法论 v2.0（详细）
├── ROADMAP.md                # 10 模块学习路线图（时间规划）
├── PROGRESS.md               # 学习进度实时追踪
│
├── code/                     # 实践代码（按模块组织）
│   ├── 01-foundations/       # 模块1：Tokenization、Attention、模型对比等
│   └── ... (02~10)
│
├── notes/                    # 专题学习笔记
├── learning-daily/           # 每日学习记录 (YYYY-MM-DD.md)
├── learning-summary/         # 周度/阶段性总结
├── assessments/              # 学习效果量化评估（主题级 + 模块级）
│
└── references/               # 参考资料索引（论文、课程、工具、博客）
```

---

## 🎯 学习模块一览

| # | 模块 | 核心内容 | 预计时长 |
|---|------|---------|---------|
| 1 | 基础概念 | Transformer、Tokenization、Attention、Agent 四要素 | 3-4 天 |
| 2 | Prompt Engineering | Few-shot、CoT、ReAct、结构化输出 | 4-5 天 |
| 3 | Tool Use / Function Calling | Tool Schema、多轮调用、错误处理 | 5-6 天 |
| 4 | RAG 检索增强生成 | Embedding、Chunking、向量检索、Reranking | 5-6 天 |
| 5 | Agent 架构模式 | ReAct、Plan-Execute、Reflexion、记忆系统 | 5-6 天 |
| 6 | 多 Agent 协作 | 通信拓扑、角色分配、任务分解 | 5-6 天 |
| 7 | MCP 协议 | Client-Server 模型、构建 MCP Server | 4-5 天 |
| 8 | 评估与监控 | 评估维度、LLM-as-Judge、Tracing | 4-5 天 |
| 9 | 生产化部署 | API 服务化、安全防护、成本优化 | 4-5 天 |
| 10 | 综合项目 | 从 0 到 1 构建完整 Agent 应用 | 7-10 天 |

---

## 🛠 技术栈

| 类别 | 工具 |
|------|------|
| 语言 | Python 3.12+ |
| 包管理 | [uv](https://docs.astral.sh/uv/) |
| LLM API | Anthropic API / OpenAI API / DeepSeek 等兼容接口 |
| 框架（按需） | LangChain / LlamaIndex / CrewAI |
| 向量数据库 | ChromaDB / Qdrant |

---

## 📝 学习方法论

本项目采用 **v2.0 学习方法论**，每节学习走 5 步循环：

1. **Step 0 — 热身运行**：先跑完整代码，建立直观感受
2. **Step 1 — 概念引入**：2-3 个关键问题，概念与代码一一对应
3. **Step 2 — 核心精讲**：代码行号串联讲解，标注知识类型
4. **Step 3 — 引导式修改**：改参数 → 加功能 → 修 bug → 扩展场景
5. **Step 4 — 费曼检验**：2-3 句话精炼复述，精准挑错

模块结束时增加 **Step 5 — 独立里程碑**（从零构建小项目，只用官方文档）。

每次 Step 4 后生成专题笔记和量化评估，确保学习可追溯、可衡量。

> 完整的教学行为准则见 [CLAUDE.md](CLAUDE.md)。

---

## 🤝 协作方式

本项目使用 **Claude Code** 作为 AI 学习伙伴，协作规范详见 [CLAUDE.md](CLAUDE.md)。Claude 严格按 5 步学习循环教学，每次提交代码附 `Co-Authored-By: Claude <noreply@anthropic.com>`。

---

> **学习是一个渐进的过程。不要急于求成，每个模块都要动手实践。记录是最好的学习方式，参考资料的可验证性是严谨性的底线。**
