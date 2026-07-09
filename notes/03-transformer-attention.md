# Transformer & Self-Attention — LLM 的核心引擎

> 创建日期：2026-06-30
> 关联模块：模块 1 — 基础概念
> 关联笔记：[[02-llm-statelessness]]（上下文理解的机制基础）、[[01-tokenization]]（Token → Embedding 的入口）、[[04-agent-four-elements]]（Agent 感知层的底层原理）
> 代码：`code/01-foundations/attention_warmup_v2.py`、`attention_step3.py`
> 评估记录：[2026-06-30 主题评估](../assessments/topic/2026-06-30-transformer-attention-assessment.md) — 🟡 基础

---

## 一句话总结

**Self-Attention 让序列中每个 token 直接"看到"所有其他 token，生成一个融合了上下文信息的新向量表示。Transformer = Self-Attention（横向通信）+ Feed-Forward（纵向加工）交替 N 层。**

---

## 核心概念

### 1. 为什么需要 Self-Attention？

RNN/LSTM 的局限：信息像"传话游戏"，第 10 个词很难记住第 1 个词的信息（长距离依赖问题）。

Self-Attention 的解法：所有词坐一张桌开会——每个词直接看所有其他词，没有距离衰减。

### 2. Q/K/V 三元组

| 角色 | 语义 | 直觉类比 |
|------|------|---------|
| Query | "我想找什么" | 搜索框里的关键词 |
| Key | "我是什么" | 视频标题/标签 |
| Value | "我的内容" | 视频实际内容 |

**关键设计**：Q/K/V 分开，让"用于匹配的表示"（Q/K）和"用于传递的表示"（V）各自独立优化。如果 Q=K=V 直接用原始 X，模型只能按语义相似度关注，学不到"追"关注"猫"这种不相似但相关的关系。

### 3. Scaled Dot-Product Attention

```
Attention(Q, K, V) = softmax(Q·K^T / √d_k) · V
```

- `Q·K^T`：计算每个词和其他词的匹配分数
- `/√d_k`：**缩放因子**。没有这个缩放，大维度下点积值太大 → softmax 变极端 → 梯度消失
- `softmax()`：把分数变成概率分布（每行求和=1）
- `·V`：用注意力权重重新加权 Value → 得到融合上下文的新向量

### 4. Multi-Head Attention

单头只看到一种关注模式。Multi-Head 并行跑多组 Q/K/V（通常 8 组），不同 head 学不同的语言模式：
- Head 1：主谓关系
- Head 2：动宾关系
- Head 3：指代关系
- Head 4：位置邻近性
- ...

### 5. 完整 Transformer 层

```
输入 → [Multi-Head Attention + Add&Norm] → [Feed-Forward + Add&Norm] → 输出（重复 N 层）
```

| 子层 | 做什么 | 通信方向 |
|------|--------|---------|
| Self-Attention | 词之间交换信息 | 横向（跨 token） |
| Feed-Forward | 每个词独立加工 | 纵向（单 token 内部） |

---

## 代码关联

| 文件 | 对应知识 |
|------|---------|
| `attention_warmup_v2.py` | Self-Attention 完整计算过程，手工设计 Q/K/V 权重演示 |
| `attention_step3.py` | 4 个实验：Temperature 锐度 → Multi-Head → Softmax 溢出 → 新句子泛化 |

**Step 3 实验关键发现**：

| 实验 | 发现 |
|------|------|
| ① Temperature | temp↓ → 注意力尖峰化（softmax 锐度控制） |
| ② Multi-Head | 不同权重产生不同但相似的模式（手工设计的局限） |
| ③ Softmax 溢出 | 不加 max 减法 → exp(1000) 溢出为 inf → nan |
| ④ 新句子 | 动词始终是"注意力磁铁"，关注主语和宾语 |

---

## 与后续模块的关联

| 知识点 | 关联模块 | 为什么重要 |
|--------|---------|-----------|
| Token → Embedding | 模块 4（RAG） | RAG 用 embedding 做语义搜索，和 attention 里的 embedding 同源 |
| Contextualized Representation | 模块 2（Prompt） | Prompt 里的每句话都会被 attention 融合——好的 prompt 结构让关键信息获得更多"注意力" |
| Multi-Head | 模块 5（Agent 架构） | 理解多 head = 多视角 → 理解多 Agent 协作中不同角色有不同"关注点" |
| Softmax + Temperature | 模块 1（基础概念） | 已学 Temperature 参数——本质是 softmax 的锐度控制 |
| 数值稳定性 | 模块 9（生产化） | 推理优化、量化等技术都涉及数值稳定性 |

---

## 开发启示（对 Agent 开发者）

> 你不用手写 Attention 层，但这些理解直接影响日常开发决策：

1. **Prompt 结构决定注意力流向**：关键指令放前面还是后面？放在 system prompt 还是 user message？——这都影响 token 之间的注意力分配
2. **Context Window 为什么有限**：Attention 的计算量是 O(n²)——n 个 token 要算 n×n 的注意力矩阵。这是 token 数不能无限大的物理原因
3. **Temperature 的本质**：你调的 temperature 参数，本质是在调 attention 输出后的 softmax 锐度——不是魔法，就是数学

---

## 参考来源

1. Attention Is All You Need (Vaswani et al., 2017) — https://arxiv.org/abs/1706.03762
2. The Illustrated Transformer (Jay Alammar) — https://jalammar.github.io/illustrated-transformer/ — 访问日期 2026-06-30
3. Lilian Weng, "Attention? Attention!" — https://lilianweng.github.io/posts/2018-06-24-attention/ — 访问日期 2026-06-30
4. [[01-tokenization]] — Token → Embedding 的入口
5. [[02-llm-statelessness]] — 上下文理解的机制基础
