---
created: 2026-07-16
module: 04-RAG
topic: embedding-basics
status: completed
评估记录: ../assessments/topic/2026-07-16-embedding-basics-assessment.md
---

# Embedding 模型基础

> 一句话总结：Embedding 将文本映射到高维语义空间中的向量，语义相近的文本向量靠近，语义无关的远离——这是 RAG 检索的数学基础。

## 核心概念

### 1. 什么是 Embedding

- Embedding 模型将任意文本转换为固定维度的**稠密向量**（dense vector）
- 每个维度没有独立的人类可理解的含义，但**方向**和**距离**联合表达了语义
- `all-MiniLM-L6-v2`：384 维，纯英文，~80MB
- `paraphrase-multilingual-MiniLM-L12-v2`：384 维，多语言，~470MB

### 2. 向量相似度

| 度量方式 | 公式 | 优点 | 缺点 |
|---------|------|------|------|
| **余弦相似度** | `cos(a,b) = a·b / (||a||·||b||)` | 只看方向，不受向量长度影响 | — |
| **欧氏距离** | `||a - b||` | 直观 | 即使方向相同，长度差异大会导致大距离 |
| **归一化欧氏** | 先 L2 归一化，再算距离 | 等价于余弦 | — |

关键：sentence-transformers 默认输出已归一化向量（||v|| = 1），此时余弦和归一化欧氏是等价的。

### 3. 语义空间的性质

- **语义聚类**：同主题的句子自然聚在一起（猫/编程/天气三组自动分离）
- **跨语言对齐**：multilingual 模型将不同语言的同义句映射到相近位置
- **词汇无关性**：相似度取决于语义位置，不取决于共享单词数

### 4. 模型选型

| 模型 | 维度 | 语言 | 大小 | 适用场景 |
|------|------|------|------|---------|
| `all-MiniLM-L6-v2` | 384 | 英文 | 80MB | 本地快速实验 |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 50+语言 | 470MB | 多语言/跨语言场景 |
| `bge-large-zh-v1.5` | 1024 | 中文为主 | 1.3GB | 中文高精度生产 |
| `text-embedding-3-small` (OpenAI) | 512/1536 | 多语言 | 云端 API | 免本地计算资源 |

## 代码关联

- `code/04-rag/embeddings/step0_warmup.py` — Step 0 热身：加载模型、编码、相似度矩阵、语义搜索
- `code/04-rag/embeddings/step3_tasks.py` — Step 3 四个任务：换模型对比、FAQ 检索、欧氏距离 Bug 修复、跨语言检索

## 与后续模块的关联

- **[[chunking-strategies]]**（下一主题）：长文本切片后每个切片独立编码为向量
- **[[vector-database]]**：海量向量如何存储和高效检索（Annoy、HNSW 索引）
- **[[retrieval-strategies]]**：Top-K、MMR、Hybrid Search 等检索优化
- **[[rag-evaluation]]**：Faithfulness、Context Relevance 等 RAG 质量评估

## 关键收获

1. Embedding = 文本 → 向量的"翻译器"，语义决定向量位置
2. 余弦相似度是 Embedding 比较的标准方式（1/(1+d) 有范围压缩问题，改用线性映射）
3. 模型选择决定语义空间的"语言能力"和精度
4. 所有 RAG 检索的核心 = 查询向量 × 文档向量 → 相似度排名

## 参考资料

1. [来源：官方文档] Sentence-Transformers Documentation — https://www.sbert.net/ — 访问日期：2026-07-16
2. [来源：模型卡] all-MiniLM-L6-v2 Model Card — https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 — 访问日期：2026-07-16
3. [来源：模型卡] paraphrase-multilingual-MiniLM-L12-v2 — https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — 访问日期：2026-07-16
