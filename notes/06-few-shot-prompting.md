# Few-shot & Zero-shot Prompting

> 创建日期：2026-07-02
> 关联模块：模块 2 — Prompt Engineering
> 关联笔记：[[02-llm-statelessness]]（无状态性是 Few-shot 能工作的前提）、[[01-tokenization]]（Token 是 Prompt 的基本计量单位）
> 代码：`code/02-prompt-engineering/few_shot_warmup.py`、`few_shot_step3.py`
> 评估记录：[2026-07-02-few-shot-prompting-assessment.md](../assessments/topic/2026-07-02-few-shot-prompting-assessment.md)

---

## 一句话总结

**Zero-shot 只给指令不给示例，Few-shot 在 Prompt 中嵌入输入→输出示例让模型模仿。Few-shot 不是模型训练——它不改变权重，只是利用 In-Context Learning 临时引导模型的输出模式。**

---

## 核心概念

### Zero-shot vs Few-shot

| | Zero-shot | Few-shot |
|------|-----------|----------|
| **做法** | 只描述任务规则 | 规则 + 标注过的输入→输出示例 |
| **模型依赖** | 完全依赖模型已有的知识和推理能力 | 模型从示例中临时"学会"你的判断模式 |
| **适用场景** | 任务定义清晰、模型本身已掌握 | 需要特定输出格式、任务定义主观、对齐期望 |
| **风险** | 模型可能误解任务意图 | 示例偏差可能诱导错误模式 |

### In-Context Learning（上下文学习）

```
Few-shot 不是训练，是"示范"：

┌─────────────────────────────────────────┐
│ 训练 / Fine-tuning（不发生在 Few-shot 中）│
│   修改模型权重 → 永久                      │
│                                          │
│ In-Context Learning（发生在 Few-shot 中）  │
│   在 context window 中展示 pattern        │
│   → 模型临时模仿 → 对话结束后消失          │
└─────────────────────────────────────────┘
```

关键认知：
- **Few-shot 示例不改变模型权重**——模型没有"学习"任何新东西
- **示例的作用是"激活"模型中已有的模式匹配能力**
- **退出对话后，示例的效果完全消失**——每次新对话都需要重新给示例
- 这就是为什么 `[[02-llm-statelessness]]` 是 Few-shot 能工作的前提：模型每次只看你给的 messages，不会"记住"上一段对话中学到的 pattern

---

## 示例偏差问题

### 发现过程（Step 0 实验）

在情感分类任务中：

| 测试句 | Zero-shot | Few-shot（3示例） | 实际情况 |
|--------|-----------|-------------------|---------|
| "等了两个小时才上菜，但是味道确实好" | 正面 ✅ | 负面 ❌ | 正面（但后面是真正评价） |

**根因**：示例 1 "等了半个小时 → 负面" 让模型学到了 `等待时长 = 负面` 这个错误的简化规则，导致它忽略"但是味道确实好"的转折。

### 三种常见的示例偏差

| 偏差类型 | 表现 | 预防方法 |
|---------|------|---------|
| **标签不平衡** | 所有示例都是同一标签 → 模型倾向输出该标签 | 每个标签至少 1 个示例 |
| **模式过拟合** | 示例覆盖的 pattern 太少 → 模型把表面特征当规则 | 覆盖不同表达方式（如"退"和"退款"都要有示例） |
| **隐形偏见** | 示例中无意引入的关联（等待=负面）→ 覆盖了真实语义 | 加入"反转"示例（前负后正 → 正面） |

> 🧠 **策略性知识**：Few-shot 的效果 = 示例质量 × 示例多样性 − 示例偏差。3 个精心挑选的示例 > 10 个同质化的示例。

---

## 核心代码模式

### 基本结构

```python
# Few-shot 的关键：在 System Prompt 中嵌入示例
FEW_SHOT_SYSTEM = """你是[角色]。请执行[任务]。

以下是示例：

示例1:
输入: "..."
输出: "..."

示例2:
输入: "..."
输出: "..."

现在请分析用户输入。只输出[格式要求]。"""
```

### 示例格式规范

```python
# ✅ 好的示例格式：清晰的输入-输出边界
"示例1:\n输入: \"...\"\n输出: \"...\""

# ❌ 差的示例格式：模糊的边界，模型可能分不清示例和指令
"比如'...'就是负面的，而'...'就是正面的"
```

### Temperature 与分类任务

```python
# 确定性任务（分类、提取）→ 低 temperature
response = client.chat.completions.create(
    model=model,
    temperature=0.0,  # 每次结果一致
)

# 创意性任务（写作、头脑风暴）→ 高 temperature
response = client.chat.completions.create(
    model=model,
    temperature=0.8,  # 输出多样化
)
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| Few-shot 示例格式 | 模块 3（Tool Use） | Function Calling 本质是"把工具定义当示例"塞给模型 |
| In-Context Learning | 模块 5（Agent 架构） | Agent 循环中每步都依赖 ICL 让模型理解当前状态 |
| Temperature 控制 | 模块 8（评估） | 评估时需要 temperature=0 保证可复现 |
| 示例偏差问题 | 模块 4（RAG） | RAG 检索到的文档本质是"动态 Few-shot 示例"——文档质量直接影响回答质量 |
| Prompt 中嵌入示例 | 模块 7（MCP） | MCP 的 Prompts 原语就是预制的 Few-shot 模板 |

---

## 实验发现总结

| 实验 | 发现 | 对应代码 |
|------|------|---------|
| Zero-shot vs Few-shot 对比 | DeepSeek V4 Flash 对反讽已有不错的 Zero-shot 理解 | `few_shot_warmup.py` |
| Temperature 实验 | temp=1.5 → 结果不稳定；temp=0.0 → 5 次完全一致 | `few_shot_step3.py` task1 |
| 示例偏差修复 | 添加"前负后正→正面"示例后，误判修复 | `few_shot_step3.py` task2 |
| 标签不平衡 Bug | 全正面示例 → 模型在任何输入上都倾向正面 | `few_shot_step3.py` task3 |
| 新场景迁移 | 6 个示例覆盖 4 个意图，4/4 全对 | `few_shot_step3.py` task4 |

---

## 参考来源

1. Anthropic API Docs — Prompt Engineering Guide — https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering
2. Lilian Weng's Blog — "Prompt Engineering" — https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/（访问日期：2026-07-02）
3. [[02-llm-statelessness]] — In-Context Learning 与无状态性的关系
4. OpenAI API Docs — Chat Completions（temperature 参数说明）— https://platform.openai.com/docs/api-reference/chat
