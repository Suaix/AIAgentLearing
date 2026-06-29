# LLM 无状态性与上下文管理

> 创建日期：2026-06-29
> 关联模块：模块 1 — 基础概念
> 关联笔记：[[tokenization]]（Token 是上下文管理的基本计量单位）
> 代码：`code/01-foundations/chat_loop.py`、`chat_loop_exercises.py`

---

## 一句话总结

**LLM 是无状态的——每次 API 调用是一次独立的前向传播。messages 数组是开发者维护的唯一外部记忆，上下文管理完全由开发者负责。**

---

## 核心心智模型

```
开发者维护的 messages 数组          模型内部（无状态）
┌─────────────────────┐           ┌──────────────────┐
│ [                   │           │                  │
│  {role: "system"},  │──发送──→  │ 前向传播 → 输出   │
│  {role: "user"},    │           │ （不保留任何记忆） │
│  {role: "assistant"},│←──返回── │                  │
│  {role: "user"},    │           └──────────────────┘
│ ]                   │
└─────────────────────┘
   ↑ 全量发送每轮历史
```

> 每次请求都必须把**全部历史消息**发给模型——模型不会"记住"上一轮说了什么。

---

## 三个关键推论

### 1. Messages 数组 = 唯一的外部记忆

| 角色 | 含义 | 谁填充 |
|------|------|--------|
| `system` | 行为约束、角色设定 | 开发者 |
| `user` | 用户输入 | 用户 |
| `assistant` | 模型回复 | API 返回 → 开发者追加到 messages |

开发者必须手动把每轮 `assistant` 回复追加到 messages，否则下一轮模型不知道它刚说过什么。

### 2. Token 随对话逐轮增长

```
第 1 轮：system(50) + user(30) = 80 prompt_tokens
第 2 轮：system(50) + user_1(30) + assistant_1(200) + user_2(40) = 320 prompt_tokens
第 3 轮：... = 560 prompt_tokens
...
```

每轮的 `prompt_tokens` = 前一轮的 `prompt_tokens + completion_tokens` + 新消息。

### 3. Context Window 是硬上限

- 每个模型有最大输入长度（如 4096、8192、128K、200K tokens）
- messages 数组不能无限增长
- 解决方案：滑动窗口裁剪、摘要压缩、向量记忆（后续模块）

---

## 实践中要解决的问题

| 问题 | 解决策略 | 对应模块 |
|------|---------|---------|
| 长对话超出 Context Window | 滑动窗口：只保留最近 N 轮 | 模块 1 ✓ |
| 重要信息被裁剪丢失 | 摘要压缩 + 长期记忆 | 模块 5 |
| Token 成本线性增长 | 消息裁剪 + 精简 Prompt | 模块 2, 9 |
| 推理模型的内部思考 | 设置足够大的 max_tokens（含 reasoning） | 模块 1 ✓ |

---

## 推理模型特殊行为

- DeepSeek V4 Pro / OpenAI o1 等推理模型在返回 `content` 前先进行内部推理
- 推理过程通过 `reasoning_content` 字段暴露（DeepSeek）
- **推理 token 计入 max_tokens 配额**——需设置足够大，否则回答被截断

---

## 关键代码模式

```python
# 基本的对话循环模式
messages = [{"role": "system", "content": system_prompt}]

while True:
    user_input = input("You: ")
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=model,
        messages=messages,  # 全量发送
    )

    assistant_msg = response.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_msg})
    # ↑ 必须手动追加，否则模型"失忆"
```

---

## 与后续模块的关联

- **模块 2（Prompt Engineering）**：System Prompt 是 messages[0]，设定整个对话的行为边界
- **模块 5（Agent 架构）**：Agent 循环（Think→Act→Observe）的每一步都是 messages 追加
- **模块 8（评估）**：评估需要追踪完整的 messages 轨迹（Tracing）

---

## 参考来源

1. OpenAI API Docs — Chat Completions — https://platform.openai.com/docs/api-reference/chat
2. DeepSeek API Docs — https://platform.deepseek.com/api-docs
3. [[tokenization]] — Token 计量与 messages 数组的 token 增长关系
