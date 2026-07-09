# 工具与框架索引

> 持续更新中 | 最后更新：2026-07-09

## LLM API 提供商

| 工具 | 说明 | 官方文档 | 试用状态 |
|------|------|---------|---------|
| Anthropic API | Claude 系列（Fable 5 / Opus 4.8 / Sonnet 4.6 / Haiku 4.5） | https://docs.anthropic.com | ⬜ |
| OpenAI API | GPT 系列模型 | https://platform.openai.com/docs | ⬜ |
| Google AI Studio | Gemini 系列（Gemini 3 Pro） | https://ai.google.dev | ⬜ |
| DeepSeek API | DeepSeek V3 / R1 系列 | https://platform.deepseek.com | 🔄 |
| Mistral API | Mistral Large / Codestral | https://docs.mistral.ai | ⬜ |

## Agent 框架

| 框架 | 特点 | 适用场景 | 官方文档 | 评估 |
|------|------|---------|---------|------|
| LangChain | 最成熟，生态丰富 | 通用 Agent 开发 | https://python.langchain.com | ⬜ |
| LangGraph | 有状态 Agent、checkpoint、time-travel 调试 | 复杂 Agent 工作流 | https://langchain-ai.github.io/langgraph/ | ⬜ |
| LlamaIndex | RAG 能力强 | 数据密集型 Agent | https://docs.llamaindex.ai | ⬜ |
| CrewAI | 角色化多 Agent（~51K⭐） | 多 Agent 协作 | https://docs.crewai.com | ⬜ |
| AutoGen (Microsoft) | ⚠️ **维护模式**（v0.7.5，2025-09 起停止新功能） | 不推荐新项目 | https://microsoft.github.io/autogen | ⏸️ |
| Microsoft Agent Framework | AutoGen 继任者，Python+.NET 双语言 | 复杂多 Agent 系统 | https://github.com/microsoft/agent-framework | ⬜ |
| Google ADK | 图工作流引擎、HITL、Go/Python/Kotlin | Google 生态 Agent | https://google.github.io/adk-docs/ | ⬜ |
| OpenAI Agents SDK | OpenAI 原生，最小抽象 | OpenAI 生态 Agent | https://github.com/openai/openai-agents-python | ⬜ |
| PydanticAI | 类型安全、验证优先 | 高质量 Agent | https://ai.pydantic.dev | ⬜ |

## MCP 相关

| 工具 | 说明 | 链接 |
|------|------|------|
| MCP 官方规范 (2025-11-25) | 当前稳定版 | https://modelcontextprotocol.io |
| MCP 2026-07-28 Draft | 下一版本（去状态化、Tasks、MCP Apps） | https://modelcontextprotocol.io/specification/draft |
| MCP Python SDK | 官方 Python SDK | https://github.com/modelcontextprotocol/python-sdk |
| MCP TypeScript SDK | 官方 TypeScript SDK | https://github.com/modelcontextprotocol/typescript-sdk |
| A2A 协议 (Google) | Agent-to-Agent 跨框架通信协议 | https://github.com/google/A2A |

## 向量数据库

| 工具 | 特点 | 适用场景 | 官方文档 |
|------|------|---------|---------|
| ChromaDB | 轻量、易上手（v0.5+ 支持 Context-1 搜索子 Agent） | 本地开发、原型 | https://docs.trychroma.com |
| Qdrant | 高性能、Rust 实现（v2.0，GPU 加速） | 生产环境首选 | https://qdrant.tech/documentation |
| Pinecone | Serverless、Nexus Agentic 引擎 | Serverless 场景 | https://docs.pinecone.io |
| Milvus | CNCF 毕业、分布式、DiskANN | 企业级十亿级规模 | https://milvus.io/docs |
| Weaviate | AI-native、 Engram 记忆层、混合搜索 | Agent 记忆系统 | https://weaviate.io/developers |
| Turbopuffer | Serverless on S3、P99<10ms | 极致性价比 | https://turbopuffer.com |

## 评估 & 监控

| 工具 | 说明 | 链接 |
|------|------|------|
| LangSmith | LangChain 配套评估平台（2026 推 Fleet 无代码 Agent Builder） | https://docs.smith.langchain.com |
| LangFuse | 开源 LLM Tracing（2026-01 被 ClickHouse 收购） | https://langfuse.com |
| Braintrust | Eval 优先的 AI 平台 | https://www.braintrust.dev |
| DeepEval | pytest 风格 Eval 框架（15K+⭐，Agent 指标） | https://docs.confident-ai.com |
| Arize Phoenix | OTel-native Tracing + 漂移检测 | https://docs.arize.com/phoenix |
| Opik (Comet) | Apache 2.0，Eval + 可观测性一体化（~20K⭐） | https://www.comet.com/docs/opik |
| FutureAGI | Apache 2.0，全栈（Eval+Observe+Gateway+Guardrails） | https://futureagi.com |

## Embedding 模型

| 模型 | 提供方 | 维度 | 特点 |
|------|------|------|------|
| text-embedding-3-small | OpenAI | 512/1536 | 性价比高（$0.02/M tokens） |
| text-embedding-3-large | OpenAI | 256/1024/3072 | 通用首选（$0.13/M tokens） |
| voyage-4-large | Voyage AI | 2048 | Anthropic 推荐，MoE 架构，共享向量空间 |
| voyage-3-lite | Voyage AI | 1024 | 性价比多语言 |
| Gemini Embedding 2 | Google | 3072 | 首个多模态 Embedding（文本+图片+音频+视频） |
| BGE-M3 | BAAI | 1024 | 开源首选，多语言，dense+sparse+multi-vector |
| Qwen3-Embedding-8B | Alibaba | 4096 | 开源 SOTA 多语言（Apache 2.0） |
| Harrier-OSS-v1 (Microsoft) | Microsoft | 640-5376 | MTEB v2 榜首（MIT） |
| Jina v5-text-small | Jina AI | 1024 | 677M 参数匹配 8B 质量（Apache 2.0） |
| Cohere Embed v4 | Cohere | 1536 | 企业级，128K 上下文，支持图像 |

---

试用状态：⬜ 待试用 | 🔄 使用中 | ✅ 已评估 | ⏸️ 暂不需
