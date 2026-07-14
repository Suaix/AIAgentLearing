# 单轮 vs 多轮 Tool 调用

> 创建日期：2026-07-14
> 关联模块：模块 3 — Tool Use / Function Calling
> 关联笔记：[[12-tool-definition]]（Agent Loop 的基础机制）、[[13-json-schema-cross-provider]]（各家工具 Schema 差异）
> 评估记录：[2026-07-14-single-vs-multi-turn-assessment.md](../assessments/topic/2026-07-14-single-vs-multi-turn-assessment.md)

---

## 一句话总结

**Agent 跑几轮不由代码分支决定，而由 LLM 每次看到工具结果后自主判断——返回 `tool_calls` 就继续循环，返回纯文本就结束。核心区别在于后续工具的调用参数是否依赖前面工具的结果。**

---

## 核心概念

### 1. 单轮调用 vs 多轮调用的本质

| 维度 | 单轮（Single-turn） | 多轮（Multi-turn） |
|------|-------------------|-------------------|
| **定义** | LLM 在发出工具调用前已掌握完成请求所需的全部信息 | LLM 必须先看到某工具的结果，才能决定下一个工具调什么、传什么参 |
| **LLM 调用次数** | 通常 2 次（第 1 次决定调工具 + 第 2 次给最终回答） | ≥ 3 次（每多一轮工具调用就多一次 LLM 回合） |
| **工具调用依赖** | 所有调用的参数可一次性确定 | 后续调用的参数依赖前面调用的结果 |
| **并行可能性** | ✅ 同一轮内独立工具可并行 | ⚠️ 仅同一轮内互相独立的工具可并行 |

**关键洞察**："单轮"还是"多轮"不由代码决定。`run_agent` 函数的循环结构是通用的：

```python
for turn in range(1, max_turns + 1):
    response = client.chat.completions.create(...)
    msg = response.choices[0].message

    if msg.tool_calls:          # ← LLM 说"我还要调工具"
        # 执行工具 → 追加结果 → continue
    else:
        return msg.content       # ← LLM 说"我回答完了"
```

**LLM 返回 `tool_calls` 还是 `content`，就是单轮/多轮的开关。**

### 2. 同一轮内的并行调用

即使只有一个轮次，LLM 也可以并行调用多个工具——前提是它们互不依赖。演示②中同时查北京+上海的天气就是例子。

```python
# 第 1 轮就并行发出 2 个 get_weather
[轮次 1] 🔧 并行调用 2 个工具：['get_weather', 'get_weather']
    → get_weather({"city": "北京"})
    → get_weather({"city": "上海"})
```

**并行条件**：LLM 能不能不看前一个工具的结果，就确定后一个工具的全部参数？能 → 并行，不能 → 分步。

### 3. 多轮调用的三种驱动因素

在 Step 3 的实践中共观察到三类多轮场景：

| 驱动因素 | 示例 | 来源 |
|---------|------|------|
| **数据依赖** | 先查天气 → 根据结果决定推荐室内还是室外景点 | 演示③ |
| **条件判断** | 距离<1500km 且下雨 → 推荐室内景点（轮 1 先算距离+天气，轮 2 再根据条件查景点） | 演示④ |
| **失败重试** | 景点返回空列表 → LLM 换参数重试 → 轮次耗尽截断 | 任务③ |

**这三种驱动因素共用同一个 Agent Loop 机制**，不需要不同的代码分支。

### 4. max_turns：多轮调用的安全阀

`max_turns` 限制了最大对话轮次。当 LLM 在失败重试中不断消耗轮次、或问题需要的轮次超过上限时，Agent 会被截断：

```python
# 任务① 实验 A：max_turns=1 截断了需要 2 轮的天气→景点链
[轮次 1] get_weather({"city": "杭州"}) → {"天气": "雨", ...}
⚠️ 达到 max_turns=1 上限，Agent 循环被截断！
```

| max_turns 过小 | max_turns 过大 |
|---------------|---------------|
| 多轮链断裂，LLM 无法完成目标 | 死循环风险（LLM 陷入重试循环）+ 成本浪费 |

**实践建议**：根据场景复杂度设 3-5 轮，单次查询设 2 轮即可。

---

## 常见陷阱

| 陷阱 | 现象 | 解决方案 |
|------|------|---------|
| 工具返回 dict 而非 JSON 字符串 | `content should be a string` API 400 错误 | 所有 mock 函数统一 `return json.dumps(...)` |
| 工具数据不完整（缺关键字段） | LLM 无法做条件判断 → 多轮链断裂或给出模糊回答 | 确保工具返回的 JSON 包含所有描述中承诺的字段 |
| LLM 在空结果上反复重试 | 轮次耗尽截断，无最终回答 | 工具返回空结果时附带原因说明（如"该城市暂无数据"），帮助 LLM 停止无效重试 |
| `max_turns` 设得太小 | 多轮链被截断 | 根据场景复杂度预估所需轮次，至少留 3 轮 |

---

## 核心代码模式

```python
# 1. 通用 Agent Loop —— 不区分单轮/多轮
def run_agent(query, tools, tool_map, max_turns=5):
    messages = [{"role": "user", "content": query}]
    for turn in range(1, max_turns + 1):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools
        )
        msg = response.choices[0].message

        if msg.tool_calls:                    # LLM 还要调工具 → 多轮继续
            messages.append(msg)
            for tc in msg.tool_calls:
                result = tool_map[tc.function.name](**json.loads(tc.function.arguments))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue                          # 回到循环，让 LLM 再次决策
        return msg.content                    # LLM 纯文本 → 结束

# 2. 多轮依赖链示例：天气 → 景点 → 餐厅（三轮）
# query = "杭州一日游：查天气 → 推荐景点 → 找附近餐厅"
# LLM 轮1: get_weather("杭州") → "雨"
# LLM 轮2: get_attractions("杭州", type="室内") → [杭州博物馆, ...]
# LLM 轮3: get_restaurants("杭州", near_attraction="杭州博物馆") → [...]
# LLM 回答

# 3. 同一轮内并行调用：不互相依赖的调用同时发出
# query = "北京和上海天气分别怎么样？"
# LLM 轮1: get_weather("北京") + get_weather("上海")  ← 并行
# LLM 回答
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| Agent Loop 机制 | 模块 5（Agent 架构） | ReAct / Plan-Execute 都基于此循环扩展 |
| 失败重试模式 | 模块 3（错误处理与重试策略） | 下一个子主题深入 |
| 并行 vs 顺序决策 | 模块 6（多 Agent 协作） | 多 Agent 的任务依赖图设计 |

---

## 参考来源

1. OpenAI API Docs — "Function Calling" — https://platform.openai.com/docs/guides/function-calling
2. [[12-tool-definition]] — Agent Loop 基础机制
3. [[13-json-schema-cross-provider]] — JSON Schema 与跨平台差异
