# JSON Schema 基础 & 跨平台 Tool Schema 差异

> 创建日期：2026-07-14
> 关联模块：模块 3 — Tool Use / Function Calling
> 关联笔记：[[12-tool-definition]]（Tool Definition 的实战模式）、[[09-json-mode-structured-output]]（JSON Schema 在结构化输出中的应用）
> 代码：`code/03-tool-use/tool_definition_warmup.py`（OpenAI 格式示例）

---

## 一句话总结

**JSON Schema 是用 JSON 写的"数据说明书"——声明一段数据应该有什么字段、什么类型、哪些必填。各家 LLM 都基于 JSON Schema 定义工具参数，但在包装结构、字段命名、类型语法和 JSON Schema 子集支持上存在差异，没有统一标准。**

---

## 核心概念

### 1. JSON Schema 是什么

JSON Schema 做的是和 Python type hints 一样的事，只不过用的是 JSON 格式，跨语言通用：

```python
# Python type hints — 只有 Python 能懂
def calculator(operation: str, a: float, b: float) -> float: ...
```

```json
// JSON Schema — 任何语言都能解析
{
    "type": "object",
    "properties": {
        "operation": { "type": "string" },
        "a":          { "type": "number" },
        "b":          { "type": "number" }
    },
    "required": ["operation", "a", "b"]
}
```

### 2. JSON Schema 三层结构

以你昨天写的 calculator 工具为例：

| 层次 | 关键字 | 作用 | 示例 |
|------|--------|------|------|
| 第 1 层：根类型 | `type` | 声明根数据是什么类型（7 种：`object` / `string` / `number` / `integer` / `boolean` / `array` / `null`） | `"type": "object"` |
| 第 2 层：字段清单 | `properties` | 逐一定义每个字段的类型和约束 | `"operation": {"type": "string"}` |
| 第 3 层：必填声明 | `required` | 列出哪些字段不能缺 | `"required": ["operation", "a", "b"]` |

### 3. Tool Use 中最常用的 6 个关键字

| 关键字 | 作用 | 使用频率 | 示例 |
|--------|------|---------|------|
| `type` | 字段数据类型 | ⭐⭐⭐⭐⭐ | `"type": "string"` |
| `properties` | 列出所有字段 | ⭐⭐⭐⭐⭐ | `"properties": { "city": {...} }` |
| `required` | 标记必填字段 | ⭐⭐⭐⭐ | `"required": ["city"]` |
| `description` | 字段的文字说明（**LLM 匹配用户意图的核心依据**） | ⭐⭐⭐⭐⭐ | `"description": "城市名称，中文或英文"` |
| `enum` | 限定取值范围 | ⭐⭐⭐ | `"enum": ["celsius", "fahrenheit"]` |
| `default` | 默认值 | ⭐⭐ | `"default": 10` |

> **掌握这 6 个关键字，足以应对 90% 的 Tool Use 场景。** 更高级的 JSON Schema 特性（`anyOf`、`$ref`、`oneOf` 等）在 Tool Use 中很少用到，且跨平台兼容性差。

---

## 跨平台差异

### 4. 三家主流平台的工具 Schema 对比

**同一个 calculator 工具，在三家要写成三种格式：**

| | OpenAI | Anthropic (Claude) | Google (Gemini) |
|---|---|---|---|
| **Schema 字段名** | `parameters` | `input_schema` | `parameters` |
| **外层包装** | `type: "function"` 嵌套 | ❌ 无包装，扁平结构 | `functionDeclarations` 数组 |
| **类型大小写** | 小写 `string` / `integer` / `number` | 小写（同 OpenAI） | **大写** `STRING` / `INTEGER` / `NUMBER` |
| **类型枚举** | `BOOLEAN` 用 `boolean` | 同 OpenAI | `BOOLEAN` |
| **nullable 表达** | `type: ["string", "null"]` | 同 OpenAI | `nullable: true`（**不同语法**） |

**代码对照：**

```python
# ── OpenAI / DeepSeek（你目前在用的格式）──
{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "执行基本数学运算",
        "parameters": {                 # ← 字段名: parameters
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    }
}

# ── Anthropic Claude ──
{
    "name": "calculator",
    "description": "执行基本数学运算",
    "input_schema": {                  # ← 字段名: input_schema；无 type:"function" 包装
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
            "a": {"type": "number"},
            "b": {"type": "number"}
        },
        "required": ["operation", "a", "b"]
    }
}

# ── Google Gemini ──
{
    "functionDeclarations": [{          # ← 包装在 functionDeclarations 数组内
        "name": "calculator",
        "description": "执行基本数学运算",
        "parameters": {                # ← 字段名: parameters；但类型全大写
            "type": "OBJECT",          # ← 大写！
            "properties": {
                "operation": {"type": "STRING", "enum": ["add", "subtract", "multiply", "divide"]},
                "a": {"type": "NUMBER"},
                "b": {"type": "NUMBER"}
            },
            "required": ["operation", "a", "b"]
        }
    }]
}
```

### 5. 响应格式差异（接收工具调用结果时）

| 维度 | OpenAI | Anthropic | Gemini |
|------|--------|-----------|--------|
| **调用标识** | `message.tool_calls[]` | `content[]` 中 `type: "tool_use"` 的块 | `parts[]` 中 `functionCall` 的块 |
| **参数格式** | `arguments` 是 **JSON 字符串**（需 `json.loads`） | `input` 是**已解析的 JSON 对象** | `args` 是**已解析的对象** |
| **结果回传** | `role: "tool"` + `tool_call_id` | `type: "tool_result"` + `tool_use_id` | `functionResponse` + `name` |
| **流式参数** | 增量字符串拼接 | `input_json_delta` 部分 JSON 拼接（三阶段生命周期） | 完整 `functionCall` 出现在 chunk 中 |

### 6. JSON Schema 子集支持差异

| JSON Schema 特性 | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| `anyOf` / `oneOf` | ⚠️ 有限支持 | ✅ 较宽松 | ⚠️ 部分支持，可能被忽略 |
| `$ref` / `$defs` | ✅ | ✅ | ❌ **不支持，必须先展开（inline）** |
| `allOf` / `if/then/else` | ✅ | ✅ | ❌ **不支持** |
| `additionalProperties` | 严格模式必须 `false` | 允许 | ❌ **会自动移除** |

> **关键陷阱**：Gemini 对 `$ref` 的支持缺失是最常见的生产事故——如果你用 `$defs` 定义可复用的类型片段，部署到 Gemini 时会收到 4xx 错误。

### 7. 行业标准化努力

**MCP（Model Context Protocol）**：Anthropic 2024 年 11 月发布，OpenAI 和 Google 后续加入。MCP 定义了一套统一格式，理论上"写一次工具定义，到处用"。

**社区翻译库**（写一种格式，自动转成各家需要的）：
- `tool-schema`（npm）— 零依赖，支持 OpenAI / Anthropic / Gemini / MCP
- `llm-rosetta`（Python）— Anthropic ↔ Gemini ↔ OpenAI 互相转换
- `ToolRegistry`（Python）— 芝加哥大学论文项目，减少 60-80% 集成代码

**实践建议**：
- 只用一家模型 → 写它的原生格式就好（你现在的 OpenAI 格式）
- 对接多家 → 以 OpenAI 格式为内部标准 + 翻译层，或直接用 MCP

---

## 与 12-tool-definition 的互补关系

| 维度 | `12-tool-definition` | `13 本笔记` |
|------|---------------------|-----------|
| 焦点 | **怎么用** Tool Definition（Agent Loop、错误处理、实战） | **是什么** 和 **差异在哪**（JSON Schema 原理、跨平台对比） |
| 知识类型 | 🔧 程序性知识 | 📝 陈述性知识 |
| 何时查阅 | 写工具调用代码时 | 理解 Schema 概念、切换模型平台时 |

---

## 参考来源

1. OpenAI API Docs — "Function Calling" — https://platform.openai.com/docs/guides/function-calling
2. Anthropic API Docs — "Tool Use" — https://docs.anthropic.com/en/docs/build-with-claude/tool-use
3. Google Gemini API Docs — "Function Calling" — https://ai.google.dev/gemini-api/docs/function-calling
4. `tool-schema` npm 包 — https://www.npmjs.com/package/tool-schema
5. ToolRegistry 论文 — "A Protocol-Agnostic Tool Management Library for Function-Calling LLMs" (2025) — https://arxiv.org/abs/2507.10593
6. [[12-tool-definition]] — Tool Definition 实战模式（Agent Loop、并行/顺序调用）
7. [[09-json-mode-structured-output]] — JSON Schema 在结构化输出中的应用
