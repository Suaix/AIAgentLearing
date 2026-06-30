# Tokenization — 文本到 Token 的转换

> 创建日期：2026-06-29
> 关联模块：模块 1 — 基础概念
> 关联笔记：[[llm-statelessness]]（Token 是 messages 数组的基本计量单位）
> 代码：`code/01-foundations/tokenization_lab.py`、`tokenization_step3.py`
> 评估记录：待评估

---

## 一句话总结

**Tokenization 是把任意文本翻译成模型能理解的整数 ID 序列的过程。Token 是 LLM 的"最小语义单位"，不是字也不是词。**

---

## 核心概念

### 1. Token ≠ 单词 ≠ 字

| 文本 | Token 数 (cl100k_base) | 说明 |
|------|------------------------|------|
| `"learning"` | 1 | 高频词 → 完整收录 |
| `"unlearning"` | 2 (`un` + `learning`) | 罕见变体 → 拆分成子词 |
| `"人工智能"` | 5 (`人` `工` `�` `�` `能`) | 中文字符未完整收录 → 字节级碎片 |
| `"ChatGPT"` | 3 (`Chat` `G` `PT`) | 专有名词 → 按常见组合拆分 |

**模型只看到整数序列**，从未"看过"文字本身：
```
"敏捷的狐狸" → [8067, 237, 15017, 115, 9554, ...] → Embedding Layer → 向量
```

### 2. BPE（Byte Pair Encoding）算法

**核心思想**：从字节级开始，统计最高频的相邻 token 对，反复合并，直到词汇表达目标大小。

```
初始状态：256 个字节 token
  ↓ 合并高频对（如 "t"+"h" → "th"）
  ↓ 再合并（如 "th"+"e" → "the"）
  ↓ 重复 N 次...
最终：100,277 个 token（cl100k_base）
```

- ✅ 高频词/子词 → 完整保留（常见英文单词、代码关键字）
- ❌ 罕见词/语言 → 退化为字节级编码（中文、Emoji、特殊符号）

### 3. 词汇表大小决定 Token 效率

| 编码器 | 使用模型 | 词汇量 | 中文"人工智能正在改变世界" |
|--------|---------|--------|---------------------------|
| `p50k_base` | GPT-3 | ~50k | 21 tokens |
| `cl100k_base` | GPT-4/3.5 | ~100k | 11 tokens |
| `o200k_base` | GPT-4o | ~200k | **5 tokens** ← 多语言优化 |

> **趋势**：词汇表越大、训练语料越多样 → token 效率越高 → 成本越低。

---

## 实践要点

### Token 计数的三个用途

1. **防止超出 Context Window**
   ```python
   if len(enc.encode(messages_text)) > model_max_context:
       messages = trim_old_messages(messages)  # 滑动窗口裁剪
   ```

2. **估算 API 成本**
   ```python
   cost = (input_tokens × input_price + output_tokens × output_price) / 1_000_000
   ```

3. **评估文档分块质量**（模块 4 RAG）
   - 每个 chunk 多少 token？是否均匀？

### 不同模型用不同 Tokenizer

- 用 tiktoken 估算 OpenAI 系列 cost（接近但不精确）
- 不同模型的 tokenizer 不可混用
- 选模型时把 tokenizer 效率纳入考量（尤其中文场景）

### Token 截断的坑

简单 `tokens[:n]` 再 `decode()` 可能产生：
- **乱码字符 `�`**：中文 UTF-8 字节被切碎
- **Token 数漂移**：decode → re-encode 后 token 数 ≠ 原始 n

**正确做法**：截断后用 while 循环回退，确保 `len(encode(result)) <= n` 且无 `�`。

---

## 关键数据

| 指标 | 值 |
|------|-----|
| cl100k_base 词汇量 | 100,277 |
| 1 个英文单词 ≈ | 1-2 tokens |
| 1 个中文字 ≈ | 1-3 tokens (cl100k) / 0.5-1 tokens (o200k) |
| 1 个 Emoji ≈ | 2-5 tokens |
| 每条消息格式开销 | ~4 tokens（OpenAI API） |
| 对话结束标记 | ~2 tokens |

---

## 与后续模块的关联

- **模块 2（Prompt Engineering）**：Prompt 措辞影响 token 消耗 → 简洁原则有成本依据
- **模块 4（RAG）**：Chunking 策略以 token 数（非字符数）为单位
- **模块 5（Agent 架构）**：记忆管理 = Token 预算管理（滑动窗口、摘要压缩）
- **模块 9（生产化）**：成本优化的底层就是 Token 优化

---

## 参考来源

1. OpenAI Cookbook — "How to count tokens with tiktoken" — https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
2. Lilian Weng, "LLM Powered Autonomous Agents" — https://lilianweng.github.io/posts/2023-06-23-agent/
3. DeepSeek API 定价 — https://platform.deepseek.com/api-docs
