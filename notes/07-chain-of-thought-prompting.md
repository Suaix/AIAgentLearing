# Chain-of-Thought (CoT) Prompting

> 创建日期：2026-07-02
> 关联模块：模块 2 — Prompt Engineering
> 关联笔记：[[06-few-shot-prompting]]（CoT 是 Few-shot 的特殊形式——教"怎么想"而非"输出什么"）、[[02-llm-statelessness]]（推理 token 也要全量发送，无状态性是 CoT 能工作的前提）
> 代码：`code/02-prompt-engineering/cot_warmup.py`、`cot_step3.py`
> 评估记录：[2026-07-02-cot-assessment.md](../assessments/topic/2026-07-02-cot-assessment.md)

---

## 一句话总结

**CoT (Chain-of-Thought) 让模型在输出最终答案前先生成推理步骤，这些推理 token 作为后续答案生成的上下文约束，从而提升多步推理任务的准确率。CoT 的价值取决于"任务难度"与"模型能力"的差距——差距越大，CoT 越有用。**

---

## 核心概念

### CoT 的 Token 级机制

```
标准 Prompting：                    CoT Prompting：
┌──────────┐                       ┌──────────────────────────┐
│ 问题     │                       │ 问题                      │
│    ↓     │                       │    ↓                      │
│ 答案     │ ← 一步跳到答案         │ 步骤1 → 步骤2 → 步骤3     │ ← 先产生推理链
└──────────┘                       │    ↓                      │
    推理不可见                      │ 答案                     │ ← 基于推理链约束生成
    无法干预                        └──────────────────────────┘
                                       推理可见 → 可检查/可调试
```

- LLM 是自回归的（autoregressive）：每个新 token 基于前面**所有已生成的 token**
- CoT 强制先生成推理 token，再生成答案 token
- 推理 token 成了答案 token 的"条件上下文"——相当于给答案加了约束
- **CoT 不是让模型变聪明，是让模型的推理过程变得可追溯、可约束**

### Zero-shot CoT vs Few-shot CoT

| | Zero-shot CoT | Few-shot CoT |
|------|--------------|-------------|
| **做法** | 加一句"Let's think step by step" | 给 1 个完整推理示例 |
| **成本** | 零示例成本，只是多了输出 token | 需要设计示例，占用 context window |
| **控制力** | 弱——只说了"要推理"，没说"怎么推理" | 强——示例定义了推理格式和粒度 |
| **泛化性** | 好——不绑定特定领域 | 示例可能引入领域偏见 |

### CoT 效果与模型能力的关系

| 模型代际 | CoT 行为 | 对 Prompt 设计的启示 |
|---------|---------|-------------------|
| **早期模型**（GPT-3.5 级别） | 中等难度题就不行了，CoT 显著提分 | CoT 是必需品 |
| **现代模型**（GPT-4o、DeepSeek V4 Flash） | 大部分题不加 CoT 也能对 | CoT 变成"保险"——难题才需要 |
| **推理模型**（o1、DeepSeek V4 Pro） | 内部自动 CoT（不可见），外部 CoT 可能干扰 | 不主动加 CoT，让模型自己推理 |

> 🧠 **策略性知识**：选择 CoT 策略前先问自己——"这个模型在这个任务上，不加 CoT 会错吗？"如果答案是"不确定"，先跑一遍标准 Prompt 再决定。

---

## 三种 CoT 常见陷阱

| 陷阱 | 表现 | 今天遇到的例子 |
|------|------|-------------|
| **不必要使用** | 对简单问题加 CoT，只增加延迟和 token 成本，不提升正确率 | Step 0 三道题，CoT 和标准 Prompt 答案一样 |
| **幻觉推理（Hallucinated Reasoning）** | 推理链看起来逻辑清晰，但中间有计算错误，结论跟着错 | 任务 ③ 验证步骤 46+48=96（应为 94），错误被模型内部推理纠正 |
| **过度模仿** | Few-shot CoT 示例太具体，模型在新问题上生搬硬套 | 未出现（模型强到不被带偏） |

---

## 核心代码模式

### Zero-shot CoT

```python
# 最简单的 CoT — 一行话
COT_PROMPT = "请一步一步地思考以下问题。最后给出明确答案。\n\n{问题}"

# 关键：temperature=0.0 保证推理过程可复现
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": COT_PROMPT}],
    temperature=0.0,
)
```

### Few-shot CoT

```python
# System Prompt 中嵌入一个"推理→答案"的完整示例
FEWSHOT_COT = """你是[角色]。请像下面的示例一样推理。

示例问题: [一个同类型问题]
示例推理:
1. [步骤1]
2. [步骤2]
...
N. 答案: [最终答案]

现在请回答用户的问题。"""
```

### CoT 与普通 Few-shot 的关系

```python
# 普通 Few-shot（上节课）：教"输出什么"
"输入: 等了半小时 → 输出: 负面"

# Few-shot CoT（这节课）：教"怎么推理"
"问题: 鸡兔同笼 → 1.设未知数 2.列方程 3.代入求解 4.验证 5.答案"
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| CoT 推理链 | 模块 3（Tool Use） | ReAct = CoT + 工具调用的交替模式 |
| 推理 token 可见性 | 模块 8（评估） | Tracing 依赖可见的推理链来判断"模型想偏了还是做错了" |
| Few-shot CoT 示例偏差 | 模块 4（RAG） | 检索到的文档 = 动态 CoT 示例 → 文档质量影响推理质量 |
| 推理模型的内部 CoT | 模块 5（Agent 架构） | Reflexion Agent 的核心是"让模型审视自己的 CoT 并修正" |

---

## 实验发现总结

| 实验 | 发现 | 关键洞察 |
|------|------|---------|
| Step 0 三题对比 | 标准/CoT/Few-shot CoT 答案一致 | DeepSeek V4 Flash 对中等难度题的推理在舒适区 |
| 任务 ① 能力边界 | 4 道递增难度题，CoT 和标准 Prompt 表现相同 | 该模型的推理边界高于这些题目的难度 |
| 任务 ② Debug CoT | 模型能识别 binary_search 的无限循环 bug | Few-shot CoT 模板对输出格式有约束作用 |
| 任务 ③ 错误推理 | 验证步骤 46+48=96 的计算错误被模型覆盖 | 强模型不会被"坏 CoT"带偏 |
| 任务 ④ 旅行规划 | CoT 模板有效引导了多约束权衡的推理结构 | CoT 在开放式决策场景仍有价值 |

---

## 参考来源

1. Wei et al. (2022) — "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" — https://arxiv.org/abs/2201.11903
2. Kojima et al. (2022) — "Large Language Models are Zero-Shot Reasoners"（Zero-shot CoT 原始论文）— https://arxiv.org/abs/2205.11916
3. [[06-few-shot-prompting]] — CoT 与普通 Few-shot 的关系
4. [[02-llm-statelessness]] — CoT 依赖无状态性（推理 token 每次都要全量发送）
