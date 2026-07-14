# Tool Definition — JSON Schema 工具定义

> 创建日期：2026-07-13
> 关联模块：模块 3 — Tool Use / Function Calling
> 关联笔记：[[09-json-mode-structured-output]]（JSON Schema 是结构化输出的基础设施）、[[08-react-prompting]]（ReAct 的 Action 步骤需要 Tool 定义来规范）、[[13-json-schema-cross-provider]]（JSON Schema 基础概念 & 各家平台 schema 差异对比）
> 代码：`code/03-tool-use/tool_definition_warmup.py`、`code/03-tool-use/tool_definition_step3.py`
> 评估记录：[2026-07-13-tool-definition-assessment.md](../assessments/topic/2026-07-13-tool-definition-assessment.md)

---

## 一句话总结

**Tool Definition 是用 JSON Schema 向 LLM 描述"外部函数长什么样"的契约文档——LLM 通过语义匹配用户意图和工具描述来决定调用哪个工具、传什么参数，但工具的实际执行完全由开发者代码完成。**

---

## 核心概念

### 1. Tool Definition 的三要素

工具定义 = LLM 能读懂的 API 文档，包含三个关键字段：

| 字段 | 作用 | 类比 |
|------|------|------|
| `name` | 函数名，LLM 用来标识"这是哪个工具" | API 端点路径 |
| `description` | 一句话说明工具的用途，**这是 LLM 判断是否调用的核心依据** | API 文档摘要 |
| `parameters` | JSON Schema 描述输入参数的名称、类型、约束 | API 参数表 |

**关键认知**：`description` 质量直接决定调用准确率。任务④中 `macbook_pro` 查询失败的根本原因就是 description 没注明产品键名格式。

### 2. Agent Loop：Tool Use 的核心循环

```
用户提问 → LLM 决策 → tool_calls? ──Yes──→ Python 执行工具 → 结果追加到消息历史 → 循环
                           │
                           No
                           ↓
                      返回最终回答
```

**每条消息都不能丢**：
- `assistant` 消息（含 `tool_calls`）：LLM 需要记住自己"刚才调了什么"
- `tool` 消息（含 `tool_call_id` + `content`）：LLM 需要看到执行结果

如果缺 `tool_call_id`，LLM 无法关联调用和结果，可能导致幻觉或错误。

### 3. 并行调用 vs 顺序调用

| 策略 | 触发条件 | 示例 |
|------|---------|------|
| 并行（一次多个 tool_calls） | 工具调用之间**无依赖关系** | 同时查北京+上海天气 |
| 顺序（多轮单次调用） | 后续调用**依赖前一步结果** | 先加后减：必须拿到和才能做减法 |

**这完全由 LLM 自主判断**——开发者不需要写任何"何时并行"的逻辑，只需要把所有可用工具都传给它。

### 4. LLM 的自我纠正能力

任务④中，LLM 第一次查 `"iPhone 16"`（带空格）失败后，自动尝试 `"iPhone16"`（无空格）并成功。这说明 LLM 能**根据工具返回的 error 信息自我纠正**——前提是 error 信息足够明确。

---

## 常见陷阱

| 陷阱 | 现象 | 解决方案 |
|------|------|---------|
| Schema 参数名与函数签名不一致 | `**arguments` 解包 KeyError | 确保 `properties` 的 key = 函数参数名 |
| 缺少 `tool_call_id` | LLM 忽略工具结果或产生幻觉 | 每条 tool 消息必须带 `tool_call_id` |
| 工具函数未处理异常 | 除零、网络超时导致崩溃 | 所有工具函数加 try-except 或边界检查 |
| `description` 太简略 | LLM 猜不到正确的调用方式 | 写明参数格式约定（如"键名小写+下划线"） |
| `required` 字段不合理 | 可选参数被强制要求，调用失败 | 只标记真正必须的参数为 required |

---

## 核心代码模式

```python
# 1. 定义工具（JSON Schema）
tool_def = {
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "这个工具做什么（LLM 靠这段文字匹配用户意图）",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "参数说明"},
            },
            "required": ["param1"],
        },
    },
}

# 2. Agent Loop
messages = [{"role": "user", "content": user_query}]
for turn in range(max_turns):
    response = client.chat.completions.create(
        model=MODEL, messages=messages, tools=[tool_def]
    )
    msg = response.choices[0].message

    if msg.tool_calls:          # LLM 要调工具
        messages.append(msg)    # ← 不能丢
        for tc in msg.tool_calls:
            result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
            messages.append({   # ← 不能丢 + tool_call_id 必须对应
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
        continue                # 继续循环
    return msg.content          # 纯文本 → 结束
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| JSON Schema 格式 | 模块 3（单轮/多轮调用） | 更复杂的工具编排基于此格式 |
| Agent Loop 模式 | 模块 5（Agent 架构） | ReAct/Plan-Execute 都复用这个循环 |
| 错误处理 | 模块 3（错误处理/超时/重试） | 下一个主题深入 |
| tool_call_id 关联 | 所有后续 Tool Use | 消息格式正确性是正确运行的前提 |

---

## 参考来源

1. DeepSeek API Docs — "Tool Calls" — https://api-docs.deepseek.com/guides/tool_calls/ — 访问日期：2026-07-13
2. OpenAI API Docs — "Function Calling" — https://platform.openai.com/docs/guides/function-calling — 访问日期：2026-07-13
3. [[09-json-mode-structured-output]] — JSON Schema 是工具定义的基础
4. [[08-react-prompting]] — ReAct 的 Action 步骤 = Tool Call
