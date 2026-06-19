# 工具与框架索引

> 持续更新中 | 最后更新：2026-06-19

## LLM API 提供商

| 工具 | 说明 | 官方文档 | 试用状态 |
|------|------|---------|---------|
| Anthropic API | Claude 系列模型 | https://docs.anthropic.com | ⬜ |
| OpenAI API | GPT 系列模型 | https://platform.openai.com/docs | ⬜ |
| Google AI Studio | Gemini 系列模型 | https://ai.google.dev | ⬜ |

## Agent 框架

| 框架 | 特点 | 适用场景 | 官方文档 | 评估 |
|------|------|---------|---------|------|
| LangChain | 最成熟，生态丰富 | 通用 Agent 开发 | https://python.langchain.com | ⬜ |
| LlamaIndex | RAG 能力强 | 数据密集型 Agent | https://docs.llamaindex.ai | ⬜ |
| CrewAI | 角色化多 Agent | 多 Agent 协作 | https://docs.crewai.com | ⬜ |
| AutoGen (Microsoft) | 对话式多 Agent | 复杂多 Agent 系统 | https://microsoft.github.io/autogen | ⬜ |
| Agno | 新兴高性能 Agent 框架 | 高性能 Agent | https://docs.agno.com | ⬜ |

## MCP 相关

| 工具 | 说明 | 链接 |
|------|------|------|
| MCP 官方规范 | Model Context Protocol 规范 | https://modelcontextprotocol.io |
| MCP Python SDK | 官方 Python SDK | https://github.com/modelcontextprotocol/python-sdk |
| MCP TypeScript SDK | 官方 TypeScript SDK | https://github.com/modelcontextprotocol/typescript-sdk |

## 向量数据库

| 工具 | 特点 | 适用场景 | 官方文档 |
|------|------|---------|---------|
| ChromaDB | 轻量、易上手 | 本地开发、原型 | https://docs.trychroma.com |
| Qdrant | 高性能、过滤强 | 生产环境 | https://qdrant.tech/documentation |
| Pinecone | 全托管、易扩展 | Serverless 场景 | https://docs.pinecone.io |
| Milvus | 分布式、大规模 | 企业级应用 | https://milvus.io/docs |

## 评估 & 监控

| 工具 | 说明 | 链接 |
|------|------|------|
| LangSmith | LangChain 配套评估平台 | https://docs.smith.langchain.com |
| LangFuse | 开源 LLM Tracing | https://langfuse.com |
| Braintrust | Eval 优先的 AI 平台 | https://www.braintrust.dev |

## Embedding 模型

| 模型 | 提供方 | 维度 | 特点 |
|------|------|------|------|
| text-embedding-3-small | OpenAI | 512/1536 | 性价比高 |
| text-embedding-3-large | OpenAI | 256/1024/3072 | 性能最强 |
| voyage-3-lite | Voyage AI | 1024 | 多语言好 |
| bge-large-en-v1.5 | BAAI | 1024 | 开源首选 |

---

试用状态：⬜ 待试用 | 🔄 使用中 | ✅ 已评估 | ⏸️ 暂不需
