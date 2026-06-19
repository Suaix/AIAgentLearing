# 学习路线图

> 创建日期：2026-06-19
> 预计总时长：10-14 周（可根据实际情况调整节奏）

## 阶段一：核心基础（第 1-2 周）

### 模块 1：基础概念 — LLM 与 Agent 概述
- **目标**：理解 LLM 基本原理和 Agent 的核心组件
- **预计时长**：3-4 天
- **关键产出**：一篇 LLM/Agent 概念总结笔记
- **子主题**：
  - [ ] Transformer 架构精要
  - [ ] Tokenization 原理与常见方法（BPE, SentencePiece）
  - [ ] Attention 机制（Self-Attention, Multi-Head, Flash Attention）
  - [ ] Agent 的四要素：感知（Perception）、规划（Planning）、执行（Action）、记忆（Memory）
  - [ ] 主流模型对比：Claude 4.x、GPT-4o、Gemini 2.5、Llama 4
  - [ ] Token 计量与成本估算

### 模块 2：Prompt Engineering
- **目标**：掌握 Prompt 设计方法，理解其作为 Agent "编程语言"的角色
- **预计时长**：4-5 天
- **关键产出**：一个 Prompt 模板库 + 实践代码
- **子主题**：
  - [ ] Few-shot / Zero-shot Prompting
  - [ ] Chain-of-Thought (CoT) & Zero-shot CoT
  - [ ] ReAct Prompting 模式
  - [ ] 结构化输出（JSON、Function Calling 格式）
  - [ ] System Prompt 设计原则
  - [ ] Prompt 版本管理与 A/B 测试思路

---

## 阶段二：Agent 关键能力（第 3-5 周）

### 模块 3：Tool Use / Function Calling
- **目标**：让 Agent 学会调用外部工具
- **预计时长**：5-6 天
- **关键产出**：一个带工具调用的 Agent Demo
- **子主题**：
  - [ ] Tool Definition（JSON Schema 规范）
  - [ ] 单轮 vs 多轮 Tool 调用流程
  - [ ] Tool 选择策略（Parallel vs Sequential）
  - [ ] 错误处理、超时、重试
  - [ ] 实践：搜索 + 计算器 + 数据库查询 Agent

### 模块 4：RAG — 检索增强生成
- **目标**：掌握 RAG 技术栈，让 Agent 能访问外部知识
- **预计时长**：5-6 天
- **关键产出**：一个文档问答系统
- **子主题**：
  - [ ] Embedding 模型选型（text-embedding-3, voyage, bge）
  - [ ] 向量数据库入门（ChromaDB / Qdrant）
  - [ ] 文档分块策略（Fixed-size, Semantic, Recursive）
  - [ ] 检索策略（Top-K, MMR, Hybrid Search, Reranking）
  - [ ] RAG 评估（Faithfulness, Relevance, Context Recall）

---

## 阶段三：Agent 架构（第 6-7 周）

### 模块 5：Agent 架构模式
- **目标**：理解 Agent 的核心架构设计
- **预计时长**：5-6 天
- **关键产出**：对比不同 Agent 架构的 Demo
- **子主题**：
  - [ ] ReAct Agent 实现
  - [ ] Plan-and-Execute Agent
  - [ ] Reflexion Agent（带自我修正）
  - [ ] 记忆系统设计（Conversation Buffer, Summary, Vector Memory）
  - [ ] Agent 框架对比与分析（LangChain, LlamaIndex, CrewAI）

### 模块 6：多 Agent 协作
- **目标**：掌握多 Agent 系统的设计方法
- **预计时长**：5-6 天
- **关键产出**：一个多 Agent 协作系统
- **子主题**：
  - [ ] 多 Agent 拓扑结构（Sequential, Hierarchical, Debate, Swarm）
  - [ ] Agent 间通信协议设计
  - [ ] 任务分解与分配
  - [ ] 实践：代码审查 + 测试生成 多 Agent 系统

---

## 阶段四：工程化（第 8-9 周）

### 模块 7：MCP — Model Context Protocol
- **目标**：掌握 MCP 协议，构建可复用的 Agent 工具服务
- **预计时长**：4-5 天
- **关键产出**：一个自建 MCP Server
- **子主题**：
  - [ ] MCP 协议架构理解
  - [ ] 三大原语：Tools、Resources、Prompts
  - [ ] 构建 MCP Server（Python SDK）
  - [ ] 与 Claude Desktop / Claude Code 集成

### 模块 8：Agent 评估与监控
- **目标**：能科学地评估 Agent 系统质量
- **预计时长**：4-5 天
- **关键产出**：一套 Agent 评估方案
- **子主题**：
  - [ ] 评估维度设计（正确性、效率、安全性、成本）
  - [ ] LLM-as-Judge 评估方法
  - [ ] Tracing（LangSmith / LangFuse）
  - [ ] Evals 数据集构建

---

## 阶段五：综合实践（第 10-12 周）

### 模块 9：生产化部署
- **目标**：了解 Agent 应用上线的关键技术点
- **预计时长**：4-5 天
- **关键产出**：部署文档 + Demo
- **子主题**：
  - [ ] API 服务化（FastAPI + Streaming）
  - [ ] 认证、限流、安全防护
  - [ ] Prompt Injection 防护策略
  - [ ] 成本优化（Prompt Caching, Token 优化）

### 模块 10：综合项目
- **目标**：从 0 到 1 构建完整 Agent 应用
- **预计时长**：7-10 天
- **关键产出**：一个可演示的完整 Agent 应用
- **项目方向建议**（选择其一）：
  - 智能编程助手（代码审查 + Bug 修复 + 测试生成）
  - 个人知识管理助手（笔记整理 + 智能检索 + 自动总结）
  - 数据分析 Agent（自然语言 → SQL/图表 → 洞察报告）

---

## 学习节奏建议

- **工作日**：每天 1-2 小时（晚间学习 + 代码实践）
- **周末**：每天 3-4 小时（集中实践 + 周度总结）
- **每完成一个模块**：停下来做一个小项目巩固
- **遇到卡点**：记录问题，先跳过，后续回头补

---

> **注意**：此路线图是指导性的，不是死板的。学习速度取决于个人基础和理解深度，质量 > 速度。
