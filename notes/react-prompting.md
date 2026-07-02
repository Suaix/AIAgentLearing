# ReAct Prompting — Reasoning + Acting

> 创建日期：2026-07-02
> 关联模块：模块 2 — Prompt Engineering
> 关联笔记：[[chain-of-thought-prompting]]（ReAct = CoT + 工具调用）、[[few-shot-prompting]]（System Prompt 中的工具声明本质上是 Few-shot 示例）
> 代码：`code/02-prompt-engineering/react_warmup.py`、`react_step3.py`
> 评估记录：[2026-07-02-react-prompting-assessment.md](../assessments/topic/2026-07-02-react-prompting-assessment.md)

---

## 一句话总结

**ReAct (Reasoning + Acting) 将模型推理与外部工具调用交替进行，模型不只是"想"，还能通过 Action 调用工具获取真实数据，再基于 Observation 继续推理——这是 AI Agent 的核心运行模式。**

---

## 核心概念

### ReAct vs CoT vs Standard

```
Standard Prompting：       CoT Prompting：            ReAct Prompting：
┌──────────┐              ┌──────────────────┐      ┌─────────────────────────┐
│ 问题     │              │ 问题              │      │ 问题                    │
│    ↓     │              │    ↓              │      │    ↓                    │
│ 答案     │              │ 步骤1 → 步骤2 → 答案│     │ Thought: 需要查什么？    │
└──────────┘              └──────────────────┘      │ Action: search_city[北京] │
    纯靠训练记忆                还是训练记忆           │    ↓ (工具执行)            │
                                                    │ Observation: 北京2188万   │
                                                    │ Thought: 还需要查深圳      │
                                                    │ Action: search_city[深圳]  │
                                                    │    ↓                     │
                                                    │ Observation: 深圳1766万   │
                                                    │ Thought: 计算倍数          │
                                                    │ Action: calculate[2188/1766]│
                                                    │    ↓                     │
                                                    │ Final Answer: 1.2倍       │
                                                    └─────────────────────────┘
                                                         真实数据来源！
```

| 维度 | Standard | CoT | ReAct |
|------|----------|-----|-------|
| 数据来源 | 训练记忆（静态） | 训练记忆（静态） | **工具返回（动态）** |
| 推理过程 | 不可见 | 可见 | **可见 + 可交互** |
| 适合场景 | 简单问答 | 多步推理 | **需要外部信息的任务** |
| 成本 | 低 | 中 | 高（多轮 API 调用） |

### ReAct 循环的四段式结构

```
┌─────────────────────────────────────────────┐
│                 ReAct Loop                   │
│                                              │
│  ┌──────────┐    ┌────────┐    ┌───────────┐│
│  │ Thought  │───→│ Action │───→│Observation││
│  │ (模型)   │    │(模型决策│   │ (代码执行) ││
│  │          │    │代码执行)│   │           ││
│  └──────────┘    └────────┘    └───────────┘│
│       ↑                                │     │
│       └────────────────────────────────┘     │
│               喂回模型继续思考                 │
│                                              │
│  终止条件：模型输出 Final Answer              │
└─────────────────────────────────────────────┘
```

**三个环节的分工（容易混淆！）**：

| 环节 | 谁做决策 | 谁实际执行 |
|------|---------|-----------|
| Thought | 模型生成 | — |
| Action | **模型**决定调用哪个工具 | **代码**解析并执行工具函数 |
| Observation | — | **代码**执行工具后返回结果 |
| Final Answer | **模型**生成 | — |

### 循环引擎的核心逻辑

```python
for turn in range(max_turns):
    reply = model.generate(messages)           # 模型输出 Thought + Action
    messages.append({"role": "assistant", ...})# 记录模型的输出
    
    action = parse_action(reply)               # 正则解析 Action
    if action:
        result = execute_tool(action)          # 真正执行工具
        messages.append({"role": "user",       # Observation 作为 user 消息喂回
            "content": f"Observation: {result}"})
        continue                                # 继续下一轮
    
    if "Final Answer:" in reply:
        break                                   # 终止
```

**关键设计决策**：
1. **Observation 用 `role: "user"`**：因为它是外部世界返回的，不是模型生成的
2. **Action 优先于 Final Answer**：即使模型同时输出两者，也先执行 Action（`continue` 跳过 break）
3. **max_turns 安全阀**：防止模型陷入无限循环

---

## 给 Agent 添加新工具的四步法

给 ReAct Agent 添加一个新工具需要改动 4 个位置（缺一不可）：

| 步骤 | 位置 | 做什么 | 示例 |
|------|------|--------|------|
| ① 数据源 | 工具函数内 | 定义数据字典/API 接口 | `KNOWLEDGE_BASE_WEATHER = {...}` |
| ② 工具函数 | 独立函数 | 实现查询/计算逻辑 | `def get_weather(query): ...` |
| ③ System Prompt | Prompt 模板 | 声明工具名 + 参数格式 | `Action: get_weather[城市名]` |
| ④ 解析路由 | 循环引擎 | 正则 + if/elif 路由 | `re.search(r"...get_weather...")` |

> ⚠️ **常见 Bug**：工具名在 Prompt、正则、路由三处拼写不一致（如 `serch_city` vs `search_city`），导致"模型输出了正确格式但工具不执行"的静默失败。

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| ReAct 循环 | 模块 3（Tool Use） | Function Calling 是 ReAct 的 API 原生实现——模型不再需要"文本解析"，API 直接返回结构化 tool_call |
| 工具定义四步法 | 模块 7（MCP） | MCP Server 本质上是"标准化工具注册协议"，和这里手动写的四步法逻辑一致 |
| 消息历史管理 | 模块 5（Agent 架构） | Agent 的记忆系统就是 messages 数组的工程化扩展 |
| Observation → user 角色 | 模块 5（Agent 架构） | Plan-and-Execute Agent 中的"执行结果喂回"遵循同样模式 |
| max_turns 安全阀 | 模块 8（评估） | Agent 步数效率是重要评估指标 |

---

## 参考来源

1. Yao et al. (2022) — "ReAct: Synergizing Reasoning and Acting in Language Models" — https://arxiv.org/abs/2210.03629
2. Anthropic API Docs — Tool Use / Function Calling — https://docs.anthropic.com/en/docs/build-with-claude/tool-use
3. [[chain-of-thought-prompting]] — CoT 是 ReAct 去掉 Action/Observation 的特例
4. [[few-shot-prompting]] — System Prompt 中的工具声明 = Few-shot 示例
