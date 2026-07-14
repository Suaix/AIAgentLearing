# Tool 选择策略 — tool_choice 与 parallel_tool_calls

> 创建日期：2026-07-14
> 关联模块：模块 3 — Tool Use / Function Calling
> 关联笔记：[[14-single-vs-multi-turn-tool-calls]]（轮次机制是本主题的基础）、[[12-tool-definition]]（工具定义格式）
> 代码：`code/03-tool-use/tool_selection_warmup.py`、`code/03-tool-use/tool_selection_step3.py`

---

## 一句话总结

**`tool_choice` 是开发者对 LLM 工具调用自由的约束——auto 放权、required 强制、none 禁止、指定工具名则精确控制。约束越紧，LLM 越可能做出无意义的工具调用。**

---

## 核心概念

### 1. tool_choice 四种模式

| 值 | 行为 | 适用场景 | 风险 |
|------|------|---------|------|
| `"auto"`（默认） | LLM 自主判断要不要调工具、调哪个 | 绝大多数场景 | 可能选择不合适的工具 |
| `"required"` | 强制必须调至少一个工具 | 确定用户的请求必须通过工具完成（如查订单号） | LLM 可能挑一个不相关的工具强行调用 |
| `"none"` | 禁止调任何工具 | 安全护栏、纯文本路由、成本优化 | 用户需要工具时无法满足 |
| `{"type":"function","function":{"name":"X"}}` | 强制调指定的工具 | 精确控制某个工具的输出格式 | 输入和工具不匹配时，LLM 强行适配导致无意义调用 |

### 2. parallel_tool_calls

| 值 | 行为 | 适用场景 |
|------|------|---------|
| `True`（默认） | 同一轮内独立工具可并行 | 提升效率，减少轮次 |
| `False` | 每轮最多调一个工具 | API 速率限制、工具有副作用需严格控制顺序 |

### 3. 约束的代价 🧠策略性

任务② 的核心发现：**同一个查询**（100+200=? + 北京天气），强制不同工具得到完全不同结果：

| 强制工具 | 结果 |
|---------|------|
| `calculator` | ✅ 算对 100+200=300，❌ 天气问题被忽略（calculator 无法查天气） |
| `translate` | ❌ 两个问题都没答案（翻译整个查询毫无意义） |

> **工具越匹配用户需求，强制约束越有效；越不匹配，LLM 越会"扭曲"用户意图来适配。**

---

## 核心代码模式

```python
# 1. 默认 auto — LLM 自由选择
client.chat.completions.create(model=MODEL, messages=messages, tools=tools)
# 等效于 tool_choice="auto"

# 2. 强制调工具 — 适合"必须走 API"的场景
client.chat.completions.create(model=MODEL, messages=messages, tools=tools,
                               tool_choice="required")
# 注意：DeepSeek 需要关闭 thinking mode

# 3. 禁止调工具 — 安全护栏
client.chat.completions.create(model=MODEL, messages=messages, tools=tools,
                               tool_choice="none")

# 4. 强制指定工具 — 精确控制
client.chat.completions.create(model=MODEL, messages=messages, tools=tools,
                               tool_choice={"type": "function", "function": {"name": "calculator"}})
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| tool_choice 路由 | 模块 5（Agent 架构） | Agent 路由器根据意图分发到不同工具集 |
| tool_choice="none" 安全护栏 | 模块 9（生产化部署） | Prompt Injection 防护的其中一层 |
| 强制工具约束 | 模块 8（评估监控） | 控制变量做对比实验 |

---

## 参考来源

1. OpenAI API Docs — "Function Calling" — https://platform.openai.com/docs/guides/function-calling
2. [[14-single-vs-multi-turn-tool-calls]] — 轮次机制基础
3. [[12-tool-definition]] — 工具定义格式
