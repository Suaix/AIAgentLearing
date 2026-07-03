# 结构化输出（JSON Mode）

> 创建日期：2026-07-03
> 关联模块：模块 2 — Prompt Engineering
> 关联笔记：[[few-shot-prompting]]（结构化输出常与 Few-shot 示例搭配）、[[react-prompting]]（ReAct 的 Action 格式也依赖结构化输出）、[[chain-of-thought-prompting]]（CoT 是推理过程结构化，JSON Mode 是输出格式结构化）
> 代码：`code/02-prompt-engineering/json_mode_warmup.py`、`json_mode_step3.py`
> 评估记录：[2026-07-03-json-mode-assessment.md](../assessments/topic/2026-07-03-json-mode-assessment.md)

---

## 一句话总结

**结构化输出（JSON Mode）是在 API 层面约束模型输出为合法 JSON 的机制——它让 LLM 的回复从"人类可读的文本"变成"程序可消费的数据"，是 Prompt Engineering 通向 Tool Use / Agent 开发的桥梁。**

---

## 核心概念

### 1. JSON Mode 的本质：解码层面的约束

JSON Mode（`response_format={'type': 'json_object'}`）不是 Prompt 技巧，而是**模型解码时 token 采样策略的改变**：

```
正常文本生成：每一步选最"通顺"的 token
JSON Mode：   额外受 JSON 语法规则约束
              { 之后必须是 key 或 }
              key 之后必须是 :
              字符串必须闭合引号
              → 不合法的 token 直接被屏蔽
```

| 对比维度 | 自由文本生成 | JSON Mode |
|---------|------------|-----------|
| 约束层 | Prompt 请求（靠模型自觉） | API 参数（硬约束） |
| 输出保证 | 模型"可能"输出 JSON | 模型"一定"输出合法 JSON |
| Temperature 影响 | 高 temperature → 格式可能崩溃 | 高 temperature → 内容多样，格式稳定 |
| 关键词要求 | 无 | DeepSeek：Prompt 中必须含 "json" |

**实验验证**：即使 temperature=2.0，JSON Mode 下也未出现解析失败——格式稳定性来自 API 层约束而非低 temperature。

### 2. 合法 JSON ≠ 符合 Schema

JSON Mode 的约束边界是**语法层**，不是**语义层**：

| 保证 | 不保证 |
|------|--------|
| ✅ 输出能通过 `json.loads()` | ❌ 字段名和你期望的一致 |
| ✅ `{` 和 `}` 配对正确 | ❌ 字段类型（`"180"` vs `180`） |
| ✅ 字符串引号闭合 | ❌ 必填字段一定存在 |
| | ❌ 值在合理范围内（如 rating > 5） |

**解决方案**：客户端双重校验

```
模型输出 → json.loads() → Pydantic/Schema 校验 → 失败则重试
         ↑ 语法层            ↑ 语义层
```

### 3. JSON Mode vs Tool Use：两个独立机制

| 维度 | JSON Mode | Tool Use (Function Calling) |
|------|-----------|---------------------------|
| API 参数 | `response_format` | `tools` |
| 作用 | 约束文本输出格式 | 定义可调用工具及其参数 schema |
| 输出 | 普通 `content` 字段（JSON 字符串） | 特殊 `tool_calls` 结构体 |
| 用途 | 信息提取、分类、结构化生成 | Agent 调用外部 API/数据库/计算 |
| 交汇点 | Tool 的 `arguments` 天然结构化 | JSON Mode 的输出可能匹配 Tool 入参 |

---

## 生产环境实践

### DeepSeek JSON Mode 特殊要求

1. **Prompt 必须含 "json" 关键字**：不含则 API 直接返回 400 错误
2. **不支持 `json_schema` 模式**：只有 `json_object`，需客户端自行校验 Schema
3. **偶现空内容**：已知 bug，建议加重试逻辑

### 健壮的 JSON 解析三步骤

```python
# 1. 去 Markdown 代码块包装
if text.startswith("```"):
    text = text[text.find("\n") + 1:]
if text.endswith("```"):
    text = text[:text.rfind("\n")]

# 2. 提取纯 JSON 子串（去掉前后废话）
start = min(text.find("{"), text.find("["))  # 注意 -1 处理
end = max(text.rfind("}"), text.rfind("]"))
text = text[start:end + 1]

# 3. 尾部逗号容错
text = re.sub(r',\s*}', '}', text)
text = re.sub(r',\s*]', ']', text)
return json.loads(text)
```

### 可复用的提取模板模式

```python
def build_extraction_prompt(schema_desc: dict) -> str:
    """Schema → Prompt 自动生成"""
    task = schema_desc["task"]
    fields = schema_desc["fields"]
    example = json.dumps({k: v for k, v in fields.items()})
    return f"你是一个信息提取助手，{task}，请以 JSON 格式输出。\nJSON 格式为：{example}"
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| JSON Schema 校验 | 模块 3（Tool Use） | Tool 的 `parameters` 定义就是 JSON Schema，模型输出的 `arguments` 天然符合 |
| 结构化输出 + 容错 | 模块 5（Agent 架构） | Agent 循环中每次工具调用返回都需解析，健壮解析是基础 |
| 模板化提取 | 模块 4（RAG） | RAG 检索后的答案合成阶段，结构化输出可控制引用格式 |
| 双重校验模式 | 模块 8（评估与监控） | Eval 框架中自动比对期望 vs 实际输出需要结构化数据 |

---

## 参考来源

1. DeepSeek API Docs — "JSON Output" — https://api-docs.deepseek.com/guides/json_mode — 访问日期：2026-07-03
2. OpenAI API Docs — "Structured Outputs" — https://platform.openai.com/docs/guides/structured-outputs — 访问日期：2026-07-03
3. [[few-shot-prompting]] — Few-shot 示例常与 JSON Mode 搭配，用示例约束输出格式
4. [[react-prompting]] — ReAct 的 Action 解析依赖结构化输出（正则匹配 Action[参数]）
