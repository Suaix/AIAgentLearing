---
created: 2026-07-16
module: 04-RAG
topic: vector-database
status: completed
评估记录: ../assessments/topic/2026-07-16-vector-database-assessment.md
---

# 向量数据库入门（ChromaDB）

> 一句话总结：向量数据库 = 向量索引（HNSW）+ 元数据过滤（where）+ 持久化存储。核心价值在大规模场景下 O(log n) 对数级检索，小规模时暴力搜索反而更快。

## 为什么选 ChromaDB 做练习

四个和学习阶段直接相关的理由：

| 理由 | 说明 |
|------|------|
| **零配置** | `pip install chromadb`，无独立服务进程。不像 Milvus 需 Docker、Qdrant 需启动 server |
| **Python-native** | API 就是 Python 函数调用，不用学新的查询语言或 gRPC 协议 |
| **可检查** | `PersistentClient` 底层是 SQLite3 + 二进制文件，可直接打开看内部 |
| **免费 + 本地** | 无云服务依赖、无 API Key、零成本 |

对比：选 Pinecone 要先注册/建 index/配网络；选 Milvus 要配 Docker + etcd + MinIO。学习阶段目标是理解向量数据库"做了什么"而非"怎么运维"——ChromaDB 摩擦最小。

## 核心概念

### 1. 什么是向量数据库

向量数据库是专门为高维向量设计的存储和检索系统。不同于传统数据库用 B-Tree 索引一维键值，向量数据库用 **ANN（近似最近邻）索引**在 384+ 维空间中快速找到最相似的向量。

| 对比维度 | 传统数据库（SQL） | 向量数据库（ChromaDB） |
|---------|-----------------|---------------------|
| 核心索引 | B-Tree（一维排序） | HNSW（多维图结构） |
| 查询方式 | `WHERE id = 5` | `query(query_embeddings=...)` |
| 结果 | 精确匹配 | Top-K 近似最近邻 |
| 元数据过滤 | `WHERE category = 'book'` | `where={"category": "book"}` |
| 典型数据量 | 百万~十亿行 | 千~亿级向量 |

### 2. ChromaDB 核心操作

```
创建 Collection  →  client.create_collection(name="xxx")
添加文档        →  collection.add(embeddings, documents, metadatas, ids)
语义查询        →  collection.query(query_embeddings, n_results=K)
元数据过滤      →  collection.query(..., where={"price": {"$lt": 1000}})
查看数据        →  collection.peek(limit=N) / collection.get()
删除            →  client.delete_collection(name)
```

### 3. 三种距离度量

| 度量 | ChromaDB 参数 | 公式 | 归一化向量下 |
|------|-------------|------|-----------|
| Squared L2 | `"l2"`（默认） | `||a-b||²` | `= 2-2cos(a,b)` |
| Cosine | `"cosine"` | `1 - cos(a,b)` | `= l2/2` |
| Inner Product | `"ip"` | `1 - a·b` | `= 1 - cos(a,b)` |

📝 关键结论：当 Embedding 模型输出归一化向量（如所有 sentence-transformers 模型），**三种度量排序完全等价**——只是对 `cos(a,b)` 做了不同的线性变换。

### 4. HNSW 索引原理（深度展开）

**HNSW = Hierarchical Navigable Small World**（分层可导航小世界图）。

直觉：在 10 万本书里找一本书 → 先看楼层导引（顶层稀疏图）→ 再看区域指示（中层）→ 最后精确到书架（底层密集图）。

具体结构：
```
第 2 层（稀疏）：  ●───────●       ← 几个"枢纽节点"，跳跃距离大
第 1 层（中等）：  ●──●──●──●     ← 中等密度
第 0 层（密集）：●─●─●─●─●─●─●   ← 所有节点，精确邻居
```

检索复杂度：O(log n)，10 万条只需 ~300-500 次距离计算（暴力搜索需 10 万次）。

### 5. 规模与性能的真实关系

| 数据量 | NumPy 暴力搜索 | ChromaDB HNSW | 谁更快 |
|--------|-------------|-------------|--------|
| < 1 万 | ~1ms（高度优化的矩阵运算） | ~5ms（索引+磁盘 I/O 开销） | **NumPy** |
| 1 万~10 万 | ~10ms | ~8ms | 差不多 |
| > 10 万 | ~100ms+（线性增长） | ~15ms（对数增长） | **ChromaDB 碾压** |
| 100 万 | ~1000ms | ~30ms | **ChromaDB 碾压** |

🧠 策略启示：小规模（< 1 万条）不需要向量数据库，NumPy/Pandas 暴力搜索足够。向量数据库的投入在规模化时才收回。

## 补充概念

### ① 向量维度锁定

ChromaDB Collection 创建后向量维度不可更改。384 维的 Collection 不能接受 768 维的向量。

🧠 策略：生产环境中在 Collection 名中标注维度和模型信息，如 `faq_v1_384d_multilingual`。

### ② Embedding 模型一致性（关键 Bug）

**入库和查询必须用同一个 Embedding 模型**。不同模型的 384 维空间语义不兼容：
- `all-MiniLM-L6-v2` 的第 0 维 ≠ `multilingual` 的第 0 维
- 维度相同、不报错 → 静默产生错误结果
- 防护：Collection metadata 中记录模型名称，或使用 Embedding 模型注册表

### ③ 持久化 vs 内存模式

```python
PersistentClient(path="./data")   # 磁盘持久化，重启保留（底层 SQLite3）
EphemeralClient()                  # 纯内存，进程退出消失
```

### ④ Pre-filtering vs Post-filtering

ChromaDB 的 `where` 过滤默认是**先过滤、再检索**（pre-filtering）：
1. 先应用元数据条件，缩小候选集
2. 在候选举上执行 ANN 向量检索
3. 返回 Top-K 结果

这样既提高效率（搜索空间缩小），又保证元数据约束严格满足。

### ⑤ ChromaDB 内部架构

```
Chromadb Client
  ├── Collection（类似 SQL Table）
  │   ├── Embedding Store（向量 + HNSW 索引）
  │   ├── Document Store（原始文本）
  │   └── Metadata Store（元数据 + SQLite3 索引）
  └── 持久化层（磁盘文件 / 内存）
```

### ⑥ 常用向量数据库全景图

| 数据库 | 类型 | 核心优势 | 适用场景 |
|--------|------|---------|---------|
| **ChromaDB** | 嵌入式/轻量 | 零配置、Python-native、Apache 2.0 | 原型开发、小规模 PoC、学习 |
| **FAISS** | 库（非数据库） | Meta 出品、极致性能、GPU 加速 | 亿级向量检索、纯算法场景 |
| **Qdrant** | 独立服务（Rust） | 高性能、丰富过滤、gRPC API | 中等规模生产、需要复杂过滤 |
| **Milvus** | 分布式云原生 | 十亿级扩展、存算分离、K8s 原生 | 企业级大规模、多租户 |
| **Weaviate** | 独立服务 | 原生混合搜索（向量+关键词）、GraphQL | 需要 BM25+向量混合检索 |
| **Pinecone** | 托管云服务 | 免运维、自动扩缩、SLA 保障 | 不想管基础设施的小团队 |
| **pgvector** | PostgreSQL 扩展 | 向量 SQL 一把梭、现有 PG 复用 | 已有 PostgreSQL 的团队 |
| **Elasticsearch** | 搜索引擎+向量 | 全文搜索+向量检索二合一 | 已有 ES 基础设施的团队 |

### ⑦ 生产环境选型决策树

```
你需要什么？
│
├─ 已有 PostgreSQL？
│   └─ YES → pgvector（零迁移成本，向量 SQL 一把梭）
│
├─ 已有 Elasticsearch？
│   └─ YES → ES 内置向量（全文+向量混合搜索开箱即用）
│
├─ 不想管服务器？
│   └─ YES → Pinecone / Zilliz Cloud（托管 Milvus）
│       └─ 预算有限？→ 先用 ChromaDB 顶着，够用就别换
│
├─ 数据量多大？
│   ├─ < 100 万条   → ChromaDB / Qdrant（单机够用）
│   ├─ 100 万~1 亿  → Qdrant / Milvus（分布式开始必要）
│   └─ > 1 亿       → Milvus / FAISS + 自建（架构决定上限）
│
├─ 需要混合搜索（BM25 + 向量）？
│   └─ YES → Weaviate / Elasticsearch
│
└─ 需要 GPU 加速？
    └─ YES → FAISS / Milvus（都支持 GPU 索引）
```

🧠 经验法则：**先用 ChromaDB 做到 10 万条，跑通全流程，再根据瓶颈换数据库。** 向量数据库之间的迁移成本远比选型决策重要——所有主流库都支持标准 ANN 算法，API 差异才是切换的真正摩擦。

## 代码关联

- `code/04-rag/vector-db/step0_warmup.py` — Step 0：创建 Collection、add、query、where 过滤、peek
- `code/04-rag/vector-db/step3_tasks.py` — Step 3：距离度量对比、过滤搜索、模型不一致 Bug、性能对比

## 与后续模块的关联

- **[[embedding-basics]]**（前序主题）：Embedding 是向量数据库的输入来源
- **[[chunking-strategies]]**（下一主题）：切分后的大量 chunk 如何存入和管理
- **[[retrieval-strategies]]**：在向量数据库基础上的高级检索（MMR、Hybrid Search）
- **[[rag-evaluation]]**：向量检索质量评估

## 参考资料

1. [来源：官方文档] ChromaDB Usage Guide — https://docs.trychroma.com/ — 访问日期：2026-07-16
2. [来源：论文] HNSW: Efficient and robust approximate nearest neighbor search — https://arxiv.org/abs/1603.09320 — 访问日期：2026-07-16
