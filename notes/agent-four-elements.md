# Agent 四要素 — 感知、规划、执行、记忆

> 创建日期：2026-06-29
> 关联模块：模块 1 — 基础概念
> 关联笔记：[[llm-statelessness]]（短期记忆 = messages 数组）、[[tokenization]]（Token 是记忆的计量单位）
> 代码：`code/01-foundations/agent_four_elements.py`、`agent_step3.py`

---

## 一句话总结

**Agent = LLM + 感知(Perception) + 规划(Planning) + 执行(Action) + 记忆(Memory)。Agent 区别于 Chatbot 的本质 = 能调用外部工具改变世界，而不只是生成文本。**

---

## 核心心智模型

```
用户输入 → [感知] 意图+实体 → [规划] 执行步骤 → [执行] 调用工具 → 结果
                ↕                 ↕                ↕
              [记忆] ←→ 短期记忆(messages数组) + 长期记忆(持久化存储)
```

---

## 四个要素详解

### 1. 感知（Perception）

**解决什么问题**：把非结构化文本 → 结构化信息（意图 + 实体）

| 实现方式 | 优点 | 缺点 |
|---------|------|------|
| if/else 规则匹配 | 快速、离线、零成本 | 覆盖不全、维护成本高 |
| **LLM 调用**（推荐） | 理解力强、可扩展 | 有延迟和成本 |

```python
# 规则版
if "天气" in user_input:
    intent = "query_weather"

# LLM 版
response = llm.chat([
    {"role": "system", "content": "识别意图，返回JSON"},
    {"role": "user", "content": user_input}
])
# → {"intent": "query_weather", "entities": {"city": "北京"}}
```

> 📝 **关键认知**：感知模块可以独立升级（规则→LLM→多模态），不影响其他组件。

### 2. 规划（Planning）

**解决什么问题**：根据意图制定执行步骤

两种模式：

| 模式 | 做法 | 适用场景 |
|------|------|---------|
| **Plan-then-Execute** | 一次生成完整计划 | 任务明确、步骤固定（查天气） |
| **ReAct（边想边做）** | 每步：思考→行动→观察→再思考 | 任务不确定、需根据结果调整（调试代码） |

```python
# Plan-then-Execute
plan = ["确认城市", "调用天气API", "格式化回复"]

# ReAct (后续模块5深入)
# Thought: 需要先查天气API → Action: call_weather_api → Observation: 晴25°C
# Thought: 用户还问了空气质量 → Action: call_aqi_api → ...
```

> 🧠 **选型策略**：确定性高 → Plan-then-Execute；不确定性高 → ReAct。

### 3. 执行（Action / Tool Use）

**解决什么问题**：实际调用外部工具完成任务（非纯文本生成）

```
AGENT 能做的                    Chatbot 不能做的
─────────────                   ──────────────
  查实时天气                      思考"天气"这个词
  执行数学计算                    猜测答案（可能错误）
  搜索最新信息                    依赖训练数据（可能过时）
  发送邮件 / 操作数据库            只能描述步骤
```

> 🔧 **本质**：执行 = Tool Use = Function Calling。这是 Agent 区别于 Chatbot 的核心差异点。

### 4. 记忆（Memory）

**解决什么问题**：维护上下文，解决 LLM 无状态性

| 记忆类型 | 对应概念 | 实现 | 容量限制 |
|---------|---------|------|---------|
| **短期记忆** | messages 数组 | list[dict]，append + 滑动窗口 | Context Window |
| **长期记忆** | 持久化存储 | 向量数据库 / KV 存储 / SQL | 几乎无限 |

```python
# 短期记忆（有容量上限，旧数据会被裁剪）
memory.add("user", "北京天气怎么样？")
memory.add("assistant", "北京天气：晴，25°C")

# 长期记忆（持久保留，不随对话轮数丢失）
memory.save_long_term("user_name", "小明")
memory.save_long_term("favorite_city", "北京")
```

> 📝 详见 [[llm-statelessness]] — LLM 无状态性决定了短期记忆必须由开发者手动管理。

---

## 四要素之间的关系

```
感知 ←──────── 规划 ←──────── 执行
  │              │              │
  └──────────── 记忆 ────────────┘
```

- **感知 → 规划**：紧耦合——知道用户想干什么才能制定计划
- **规划 → 执行**：紧耦合——计划直接决定执行步骤
- **记忆 ↔ 全部**：松耦合——每个环节读写记忆，但各自独立运作

> **设计原则**：拆成四要素不是为了分类，而是为了**独立优化**：
> - 换更好的感知模型 → 不影响规划/执行
> - 加向量数据库做长期记忆 → 不影响感知/执行
> - 换更快的 Tool Use 框架 → 不影响感知/规划

---

## 与后续模块的关联

| 要素 | 对应后续模块 |
|------|------------|
| 感知 | 模块 2（Prompt Engineering）— System Prompt 约束感知行为 |
| 规划 | 模块 5（Agent 架构）— ReAct、Plan-Execute 深入实现 |
| 执行 | 模块 3（Tool Use）— JSON Schema 定义、错误处理、重试 |
| 短期记忆 | 模块 5 — 滑动窗口、摘要压缩、对话缓冲策略 |
| 长期记忆 | 模块 4（RAG）— 向量数据库、检索增强 |

---

## 参考来源

1. Lilian Weng, "LLM Powered Autonomous Agents" — https://lilianweng.github.io/posts/2023-06-23-agent/ — 提出 Agent = Planning + Memory + Tool Use 框架
2. ReAct Paper (Yao et al., 2022) — https://arxiv.org/abs/2210.03629
3. [[llm-statelessness]] — 短期记忆与 messages 数组的关系
4. [[tokenization]] — Token 计数对记忆管理的影响
