# 检索策略（Retrieval Strategies）

> 创建日期：2026-07-22
> 关联模块：模块 4 — RAG（检索增强生成）
> 关联笔记：[[embedding-basics]]（检索依赖 Embedding 将查询和文档映射到同一向量空间）、[[vector-database]]（向量数据库提供检索的存储和查询基础设施）、[[chunking]]（分块质量决定了检索精度的上限——Garbage In, Garbage Out）
> 代码：`code/04-rag/retrieval-strategies/step0_warmup.py`、`code/04-rag/retrieval-strategies/step3_tasks.py`
> 评估记录：[2026-07-22-retrieval-strategies-assessment.md](../assessments/topic/2026-07-22-retrieval-strategies-assessment.md)

---

## 一句话总结

**检索策略是在向量数据库中"怎么找"的方法集合——从简单的 Top-K 相似度取前几名，到 MMR 平衡多样性与相关性，到混合搜索融合语义和关键词信号，再到两阶段检索用 Cross-Encoder 精排。核心权衡始终是：准确性 vs 延迟 vs 多样性。**

---

## 核心概念

### 四种检索策略全景

| 策略 | 核心思想 | 计算复杂度 | 准确性 | 多样性 | 适用场景 |
|------|---------|-----------|--------|--------|---------|
| A. Top-K 语义搜索 | 纯向量相似度，取前 K | O(N·D) 点积 | ★★★ | ⭐（无控制） | 简单 FAQ 问答 |
| B. MMR | 贪心选择：相关性 − 与已选文档的相似度惩罚 | O(K·N²)（含预计算矩阵） | ★★★☆ | ★★★★ | 推荐系统、探索式搜索 |
| C. 混合搜索（Hybrid） | 语义分数 + 关键词分数，加权或 RRF 融合 | 取决于融合方式 | ★★★★ | ★★★ | 有专业术语/实体的领域 |
| D. 两阶段重排序 | 粗筛（Bi-Encoder，快）→ 精排（Cross-Encoder，准） | O(N·D) + O(C·CE) | ★★★★★ | ★★★ | 法律、医疗、高精度问答 |

### Top-K 语义搜索

最基础的检索方式：
1. 用同一个 Bi-Encoder 编码 query 和所有 doc
2. 计算 query 向量与每个 doc 向量的余弦相似度
3. 取相似度最高的 K 个

**优势**：极快（doc 向量可预计算缓存）、简单
**劣势**：可能返回 3 条内容几乎相同的文档（如 Top-3 全是"退货"相关），缺乏多样性

### MMR（Maximal Marginal Relevance）

MMR = argmax_{D_i ∉ S} [λ · sim(D_i, Q) − (1-λ) · max_{D_j ∈ S} sim(D_i, D_j)]

| 参数 | 含义 | λ→1.0 | λ→0.0 |
|------|------|--------|--------|
| λ | 相关性权重 | 退化为 Top-K | 极度分散（首条随机，后续刻意回避） |
| 1-λ | 多样性权重 | 几乎忽略与已选文档的相似度 | 主导选择 |

**贪心选择过程**（以 FAQ 为例）：
1. 第 1 轮（无已选文档，多样性惩罚=0）：选最相关的 [#0 退货政策]
2. 第 2 轮：#1 换货流程 和 #0 高度相似（同属退换货）→ 惩罚大；#2 支付方式 相似度低但和 #0 完全不同主题 → 惩罚小 → MMR 综合分更高 → 选 #2
3. 第 3 轮：在两者已选的基础上继续贪心

**生产环境推荐 λ=0.6~0.8**——太低导致用户困惑"为什么推荐了不相关的东西"，太高等于没用 MMR。

### 混合搜索（Hybrid Search）

**动机**：纯语义搜索擅长"便宜"↔"实惠"这种同义替换，但在精确匹配（产品型号、专有名词、数字）上表现差。关键词搜索刚好相反。

**融合方法对比**：

| 方法 | 原理 | 优势 | 劣势 |
|------|------|------|------|
| 分数归一化+加权 | min-max 归一化后线性加权 | 简单直观 | 极端分数分布时归一化放大噪声 |
| RRF（Reciprocal Rank Fusion） | Σ 1/(k+rank_i)，只关心排名 | 对异构分数鲁棒 | 丢失"排名差距大/小"的信息 |
| 学习型融合 | 训练一个小模型来预测最佳权重 | 最优 | 需要标注数据 |

**RRF 公式**：RRF(d) = Σ 1/(k + rank_i(d))，k=60（标准平滑常数）

为什么 k=60？k=0 时 1/1 vs 1/2 = 1.0 vs 0.5（排名差一位，分数差一倍）；k=60 时 1/61 vs 1/62 ≈ 0.0164 vs 0.0161（差距合理平滑）。排名第 1 和第 2 在实际效果上往往差不多，k=60 防止了过度惩罚。

### 两阶段检索（Bi-Encoder → Cross-Encoder）

这是工业界 RAG 系统的标准架构。

**Bi-Encoder（双编码器）**：
- Query 和 Doc 各自独立编码成向量
- Doc 向量可提前计算并缓存于向量数据库
- 检索时只编码 query（1 次推理）+ N 次向量点积（纯数学，极快）
- 弱点：query 和 doc 编码过程互不可见，384 维向量要"预判"所有可能的查询→信息压缩损失

**Cross-Encoder（交叉编码器）**：
- Query 和 Doc 拼接成一个序列输入 Transformer
- 注意力机制在 query 的每个词和 doc 的每个词之间自由流动
- 弱点：每对 (query, doc) 都是一次完整推理——100 万篇文档 = 100 万次推理，不可接受

**为什么必须是两阶段**：
- 全用 Bi-Encoder → 准确度不够（实验可见：CE 把粗筛第 6 名提到精排第 1 名）
- 全用 Cross-Encoder → 延迟不可接受
- 两阶段结合 → 召回用 Bi-Encoder（100 万→100），精排用 CE（100→10），在延迟和准确性间取最优平衡

![检索流程]
```
用户查询 → Bi-Encoder 编码 query
                ↓
         向量数据库（预存了所有 doc 向量）
           Bi-Encoder 粗筛 Top-C（C≈2~3K）
                ↓
          Cross-Encoder 精排 Top-C → Top-K
                ↓
          返回最终 Top-K 结果
```

### 查询扩展（Query Expansion / PRF）

**伪相关反馈（Pseudo Relevance Feedback）**：
1. 用户输入短查询 → 初次检索 Top-K
2. 假设这 K 个结果是"相关"的（伪相关）
3. 从这些结果中提取高频关键词
4. 将关键词追加到原始查询 → 二次检索

**局限性**：Garbage In, Garbage Out——如果初次检索就偏了（如"运费"的最相关文档居然是"会员积分"），扩展只会放大错误方向。

**生产环境的改进**：
- 使用 jieba/pkuseg 等中文分词工具提取真正有意义的词语（而非 2-gram 字符片段）
- 引入多样性约束（不是频率最高的就最好——"的"、"是"频率高但无用）
- 结合用户点击反馈（真实相关反馈 > 伪相关反馈）

---

## 密集检索 vs 稀疏检索

| 维度 | 密集检索（Dense） | 稀疏检索（Sparse） |
|------|-------------------|-------------------|
| 代表方法 | Bi-Encoder / Embedding | BM25 / TF-IDF |
| 原理 | 将文本映射到稠密向量空间 | 基于词频统计的倒排索引 |
| 优势 | 捕获语义相似（"退"↔"退款"↔"退货"） | 精确匹配专有名词和数字 |
| 劣势 | 缩写、型号等精确匹配差 | 同义词覆盖不了 |
| 存储 | 向量数据库（高维浮点向量） | 倒排索引（少量内存/磁盘） |
| 最佳实践 | **混合搜索 = 两者互补** | |

---

## 核心代码模式

```python
# MMR 贪心选择的核心公式
mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty
# λ↑ → 偏相关性（更多相似结果）
# λ↓ → 偏多样性（覆盖面更广）

# RRF 融合的核心公式（k=60 为平滑常数）
rrf_score = 1/(k + rank_semantic) + 1/(k + rank_keyword)
# 不关心原始分数大小，只关心相对排名
# 对异构来源（语义搜索 + BM25 + 点击率）极度鲁棒

# 两阶段检索
candidates = vector_db.search(query_emb, top_c=C)   # 粗筛
pairs = [(query, doc) for doc in candidates]
ce_scores = cross_encoder.predict(pairs)              # 精排
final = sorted(zip(candidates, ce_scores), key=...)[:K]
```

---

## 检索评估指标

| 指标 | 含义 | 何时关注 |
|------|------|---------|
| **Recall@K** | 正确答案出现在 Top-K 中的概率 | 不想漏掉任何相关信息 |
| **MRR**（Mean Reciprocal Rank） | 第一个正确答案排名的倒数均值 | 关心"第一个正确答案"的位置 |
| **NDCG**（Normalized DCG） | 考虑排名位置 + 多级相关性的指标 | 有"部分相关"vs"高度相关"之分 |

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| 两阶段检索架构 | 模块 5（Agent 架构） | Agent 需要决策"何时用哪种检索策略"——这是工具选择的一部分 |
| RRF 多源融合 | 模块 5（Agent 架构） | Agent 可能同时查询向量库 + API + 本地文件，需要融合异构结果 |
| 检索评估指标 | 模块 8（评估与监控） | RAG 系统的评估 pipeline 核心就是 Recall/MRR/NDCG 的自动化计算 |
| Cross-Encoder 精排 | 模块 8（评估与监控） | LLM-as-Judge 评估时也用到 Cross-Encoder 作为轻量级评判器 |

---

## 参考来源

1. Carbonell & Goldstein (1998) — "The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries" — https://doi.org/10.1145/290941.291025
2. Cormack et al. (2009) — "Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods" — https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
3. Sentence-Transformers 官方文档 — "Cross-Encoders" — https://www.sbert.net/examples/applications/cross-encoder/README.html
4. [[embedding-basics]] — Embedding 模型基础（检索的向量化基础）
5. [[vector-database]] — 向量数据库入门（检索的存储和查询基础设施）
6. [[chunking]] — 文档分块策略（检索精度的上游依赖）
