# 文档分块策略（Chunking）

> 创建日期：2026-07-20
> 关联模块：模块 4 — RAG（检索增强生成）
> 关联笔记：[[embedding-basics]]（分块后的文本由 Embedding 模型编码）、[[vector-database]]（分块结果存入向量数据库）
> 代码：`code/04-rag/chunking/step0_warmup.py`、`code/04-rag/chunking/step3_tasks.py`
> 评估记录：[2026-07-20-chunking-assessment.md](../assessments/topic/2026-07-20-chunking-assessment.md)

---

## 一句话总结

**文档分块是将长文本切割成语义合理的短片段，以平衡检索精度和上下文完整性的 RAG 预处理步骤。它是整个 RAG 系统中工程决策最密集的环节——没有普适的"最佳参数"，必须在具体数据上评测。**

---

## 核心概念

### 为什么需要分块：信号稀释（Signal Dilution）

整篇文档编码为一个向量时，Embedding 被迫"平均代表"所有主题。如果文档包含 N 个不同主题，每个主题的信号只占向量的 ~1/N，导致任何查询的相似度都被大量噪声稀释。

| | 整篇不分块 | 合理分块 |
|---|---|---|
| RAG 查询相似度 | 0.063 | 0.635 |
| 信噪比 | ~10% | ~90% |

### 四种分块策略

| 策略 | 原理 | 适用场景 | 复杂度 |
|------|------|---------|--------|
| **固定大小** | 按字符/token 数切分 | 通用，最简单 | O(n) |
| **句子级** | 按句子边界，保持语法完整 | 自然语言文本 | O(n) |
| **语义分块** | 用 Embedding 相似度检测"主题转换点" | 异构长文档（论文、报告） | O(n·d) |
| **递归/层级** | 按段落→句子→短语逐级切分 | 代码、结构化文档 | O(n log n) |

### 语义分块（Semantic Chunking）— 核心算法

```
算法：
  1. 对所有句子编码 → embeddings[N, dim]
  2. for i in 1..N-1:
       sim = cos(embeddings[i-1], embeddings[i])
       if sim < threshold:  # 主题转换
         切分（当前块归档，开始新块）
       else:
         sentences[i] 归入当前块
  3. 归档最后一个块
```

**关键洞察**：语义分块本质上是对相邻句子做**一维聚类**——相似的合并，不相似的切分。threshold 是聚类敏感度：越低 → 越粗 → 块越大；越高 → 越细 → 块越小。

**阈值困境**：没有普适的最佳 threshold。
- "AI Agent" 和 "Tool Use" 句间相似度 0.47
- 设 threshold=0.4 → 两句合并 → 信号稀释，检索精度下降
- 设 threshold=0.5 → 两句分离 → 上下文断裂
- 正确答案取决于查询和文档，必须用数据做 grid search

### 三难权衡

```
        检索精度（Precision）
             /\
            /  \
           / ⚖️ \
          / 最优区 \
         /__________\
  召回率              上下文完整性
  (Recall)          (Context Adequacy)
```

- **切太小**：精度高，但 LLM 只看到碎片，丢失跨句关联
- **切太大**：上下文完整，但信号稀释
- **起始建议**：256-512 tokens（约 200-400 中文字），10-20% 重叠

### Chunk Overlap（块重叠）

滑动窗口中相邻块共享内容。10-20% 的 overlap 可防止关键信息恰好落在块边界上。

**代价**：20% overlap ≈ 20% 的额外存储和计算。不需要重叠的场景：FAQ（每问独立）、产品列表（每个条目独立）。

### Bi-Encoder vs Cross-Encoder（重排序）

这是理解 RAG 两阶段检索架构的核心：

| | Bi-Encoder（粗检索） | Cross-Encoder（精排） |
|---|---|---|
| 编码方式 | 查询和文档**分开**编码 | 查询和文档**拼接后一起**编码 |
| 能否预计算 | ✅ 文档向量可预先存储 | ❌ 必须实时计算每对 (q, d) |
| 速度 | O(1) · N（查 N 个文档） | O(N) · 模型推理 |
| 语义精度 | 🟡 粗（未见过的词关联可能漏） | 🟢 精（Attention 捕获深层语义） |
| 检索 100 万文档 | ~10ms | ~100 小时 |
| 排序 100 候选 | ~1ms | ~100ms |
| 代表模型 | `all-MiniLM-L6-v2`、`text-embedding-3` | `bge-reranker-v2-m3`、`cross-encoder/ms-marco` |

**为什么需要两步？**
- 阶段 1（Bi-Encoder）：从百万级文档中快速召回 Top-100，不可能全部用 Cross-Encoder
- 阶段 2（Cross-Encoder）：对 100 个候选精细打分重排，解决"部署 ↔ MLOps"这种语义关联漏检

### Chunk Size 的 Token 视角

生产环境中关心 Token 数而非字符数：
- Embedding 模型有最大输入限制（`all-MiniLM-L6-v2`：256 tokens）
- LLM 上下文窗口需容纳检索到的 N 个块
- **经验公式**：`chunk_tokens × top_k ≤ context_window × 0.5`

---

## 实验发现（Step 0 & Step 3）

### chunk_size 对检索的影响

| chunk_size | "RAG"查询 Top-1 相似度 | 现象 |
|---|---|---|
| 1 | 0.635 | 纯净的 RAG 定义句 |
| 2 | 0.635 | 同上（RAG 定义恰好 2 句） |
| 3 | **0.393** | 混入 MLOps 句，稀释 40% |
| 5 | 0.635 | 恢复——整段 RAG+MLOps+...但 Top-1 恰好是 RAG 块 |

**关键发现**：相似度随 chunk_size 的变化是**非单调**的——取决于文档结构。chunk_size=3 时 RAG 被 MLOps 拖累，但 chunk_size=5 又因为排序变化而恢复。这说明 chunk_size 没有"越大越好"或"越小越好"的规律。

### 滑动窗口的陷阱

滑动窗口在 RAG 查询上反而不如固定分块（0.393 vs 0.635），因为窗口重叠强制不相关的句子（MLOps + RAG）合并，反而引入噪声。**滑动窗口在相邻句子主题关联强时才有价值**。

### 语义分块 vs 固定分块（新文档）

语义分块（threshold=0.4）在 "什么是 Tool Use？" 查询上惨败（0.46 vs 0.74），因为它将 AI Agent 概念和 Tool Use 合并到一个大块中，导致与固定分块的纯净 Tool Use 块对比时信号被稀释。

---

## 核心代码模式

```python
# 模式 1：固定大小分块
def fixed_chunk(sentences: list[str], chunk_size: int) -> list[str]:
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = "。".join(sentences[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# 模式 2：语义分块
def semantic_chunk(sentences, model, threshold):
    embeddings = model.encode(sentences)
    chunks, current = [], [sentences[0]]
    for i in range(1, len(sentences)):
        sim = cosine_similarity(embeddings[i-1], embeddings[i])
        if sim < threshold:  # 主题边界
            chunks.append("。".join(current))
            current = []
        current.append(sentences[i])
    chunks.append("。".join(current))
    return chunks

# 模式 3：可配置检索器
def build_retriever(sentences, strategy, model, query, top_k=3, **kwargs):
    if strategy == "fixed":
        chunks = fixed_chunk(sentences, kwargs.get("chunk_size", 2))
    elif strategy == "sliding":
        chunks = sliding_chunk(sentences, kwargs.get("chunk_size", 2),
                               kwargs.get("overlap", 1))
    else:  # semantic
        chunks = semantic_chunk(sentences, model, kwargs.get("threshold", 0.5))
    results = retrieve(query, chunks, model)
    return results[:top_k]
```

---

## 与后续模块的关联

| 知识点 | 后续模块 | 关联说明 |
|--------|---------|---------|
| 分块策略选择 | 模块 5（Agent 架构） | Agent 的 RAG 工具需要根据文档类型自动选择分块参数 |
| 检索精度 vs 召回 | 模块 8（评估与监控） | Chunking 参数是 RAG 评估实验的关键自变量 |
| 语义分块的 threshold | 模块 9（生产化部署） | 生产环境中需要针对不同文档类型维护不同的分块配置 |
| Cross-Encoder 重排序 | 模块 8（评估与监控） | Reranker 是 RAG 评估 pipeline 的重要组成部分 |

---

## 参考来源

1. LlamaIndex — "Chunking Strategies" — https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/ — 访问日期：2026-07-20
2. LangChain — "Text Splitters" — https://python.langchain.com/docs/modules/data_connection/document_transformers/ — 访问日期：2026-07-20
3. Pinecone — "Chunking Strategies for RAG" — https://www.pinecone.io/learn/chunking-strategies/ — 访问日期：2026-07-20
4. [[embedding-basics]] — Embedding 模型与相似度计算
5. [[vector-database]] — 分块后的向量存储与检索
