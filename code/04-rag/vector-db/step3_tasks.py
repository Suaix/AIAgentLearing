"""
Step 3 — 向量数据库引导式修改
四个渐进任务，通过命令行参数选择：
  uv run python code/04-rag/vector-db/step3_tasks.py 1    # 任务①
  uv run python code/04-rag/vector-db/step3_tasks.py 2    # 任务②
  uv run python code/04-rag/vector-db/step3_tasks.py 3    # 任务③
  uv run python code/04-rag/vector-db/step3_tasks.py 4    # 任务④
"""

import sys
import time
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

# ══════════════════════════════════════════════════════════════
# 公共工具
# ══════════════════════════════════════════════════════════════

CHROMA_PATH = "./chroma_data_step3"


def get_fresh_client():
    """获取客户端并清理旧数据"""
    import shutil, os

    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    return chromadb.PersistentClient(path=CHROMA_PATH)


def create_collection_with_docs(client, name, documents, metadatas, model):
    """辅助：创建 collection 并添加文档"""
    try:
        client.delete_collection(name)
    except Exception:
        pass
    collection = client.create_collection(name=name)
    if documents:
        embeddings = model.encode(documents).tolist()
        ids = [f"{name}_{i}" for i in range(len(documents))]
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
    return collection


# ══════════════════════════════════════════════════════════════
# 任务① — 改参数：对比三种距离度量
# ══════════════════════════════════════════════════════════════


def task1_distance_metrics():
    """
    任务目标：对比 ChromaDB 三种 distance 函数对查询结果的影响

    背景：ChromaDB 在创建 collection 时可以通过 metadata 指定距离度量。
          默认是 "l2" (squared L2)，还有 "cosine" 和 "ip" (inner product)。
    """

    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = get_fresh_client()

    # 一组简单的英文句子
    documents = [
        "The weather is sunny and warm today",
        "It is raining heavily outside",
        "Machine learning is transforming industries",
        "Deep learning uses neural networks",
        "I enjoy hiking in the mountains",
        "Python is a popular programming language",
    ]
    metadatas = [{"source": "test"} for _ in documents]

    metrics = ["l2", "cosine", "ip"]

    # TODO ①-2：重新用正确的 metadata 创建三个 collection，分别用 l2/cosine/ip
    #           每个 collection 存入相同的 documents
    #           然后用 "artificial intelligence and data science" 查询
    #           对比三个 collection 返回的 top-3 结果和距离值有何不同
    #
    # 提示代码骨架：
    # for metric in ["l2", "cosine", "ip"]:
    #     col = client.create_collection(
    #         name=f"dist_{metric}",
    #         metadata={"hnsw:space": metric}
    #     )
    #     embeddings = model.encode(documents).tolist()
    #     col.add(embeddings=embeddings, documents=documents,
    #             metadatas=metadatas, ids=[f"d{i}" for i in range(len(documents))])
    #     query_emb = model.encode(["artificial intelligence and data science"]).tolist()
    #     results = col.query(query_embeddings=query_emb, n_results=3)
    #     print(f"\n   metric={metric}:")
    #     for i in range(3):
    #         print(f"   #{i+1} dist={results['distances'][0][i]:.4f} | {results['documents'][0][i]}")
    for metric in metrics:
        col = client.create_collection(
            name=f"dist_{metric}", metadata={"space": metric}
        )
        embedding = model.encode(documents).tolist()
        col.add(
            embeddings=embedding,
            documents=documents,
            metadatas=metadatas,
            ids=[f"d{i}" for i in range(len(documents))],
        )
        query_emb = model.encode(["artificial intelligence and data science"]).tolist()
        results = col.query(query_embeddings=query_emb, n_results=3)
        print(f"\n metric={metric}")
        for i in range(3):
            print(
                f"   #{i+1} dist={results['distances'][0][i]:.4f} | {results['documents'][0][i]}"
            )

    # TODO ①-3：观察输出，写一行注释说明：
    #           哪种度量的距离值范围最直观？为什么 l2 和 cosine 对归一化向量等价？
    #
    # 你的发现：
    # ip的更直观


# ══════════════════════════════════════════════════════════════
# 任务② — 加功能：构建可过滤的产品搜索
# ══════════════════════════════════════════════════════════════


def task2_filtered_search():
    """
    任务目标：构建一个带分类过滤的电商产品搜索

    场景：用户输入搜索词 + 选择品类，系统只在指定品类中检索相关产品。
    """

    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    client = get_fresh_client()

    # 产品数据库
    products = [
        # 电子产品
        (
            "iPhone 15 Pro Max 256GB 钛金属原色",
            {"category": "电子产品", "brand": "Apple", "price": 8999},
        ),
        (
            "MacBook Air M4 芯片 15英寸 16GB+512GB",
            {"category": "电子产品", "brand": "Apple", "price": 9499},
        ),
        (
            "Sony WH-1000XM6 头戴式降噪耳机 铂金银",
            {"category": "电子产品", "brand": "Sony", "price": 2499},
        ),
        (
            "Nintendo Switch 2 游戏主机 续航版",
            {"category": "电子产品", "brand": "Nintendo", "price": 2599},
        ),
        # 图书
        (
            "深入理解计算机系统（原书第4版）",
            {"category": "图书", "brand": "机械工业出版社", "price": 139},
        ),
        (
            "设计模式：可复用面向对象软件的基础",
            {"category": "图书", "brand": "机械工业出版社", "price": 69},
        ),
        (
            "Python编程：从入门到实践（第3版）",
            {"category": "图书", "brand": "人民邮电出版社", "price": 89},
        ),
        (
            "机器学习实战：基于Scikit-Learn和TensorFlow",
            {"category": "图书", "brand": "O'Reilly", "price": 119},
        ),
        # 运动户外
        (
            "Nike Air Zoom Pegasus 42 男款跑步鞋",
            {"category": "运动户外", "brand": "Nike", "price": 899},
        ),
        (
            "探路者冲锋衣男女三合一可拆卸户外登山服",
            {"category": "运动户外", "brand": "探路者", "price": 599},
        ),
        (
            "Yeti Rambler 保温杯 不锈钢真空 591ml",
            {"category": "运动户外", "brand": "Yeti", "price": 299},
        ),
    ]

    docs = [p[0] for p in products]
    metas = [p[1] for p in products]

    col = client.create_collection(name="products")
    embeddings = model.encode(docs).tolist()
    col.add(
        embeddings=embeddings,
        documents=docs,
        metadatas=metas,
        ids=[f"p{i}" for i in range(len(docs))],
    )

    print(f"\n📦 产品数据库已创建：{col.count()} 条产品")

    # TODO ②-1：完成以下查询逻辑——
    #           用户搜索 "轻便笔记本电脑"，不限制品类，返回 top-3
    query_text = "轻便笔记本电脑"
    query_emb = model.encode([query_text]).tolist()
    results = col.query(query_embeddings=query_emb, n_results=3)
    # 打印结果
    for i in range(len(results["ids"][0])):
        print(
            f"   #{i+1} dist={results['distances'][0][i]:.4f} | {results['documents'][0][i]}"
        )

    # TODO ②-2：用户搜索 "编程学习书籍"，但只想看 "图书" 品类，返回 top-3
    #           提示：使用 where={"category": "图书"}
    query_text = "编程学习书籍"
    query_emb = model.encode([query_text]).tolist()
    results = col.query(
        query_embeddings=query_emb, n_results=3, where={"category": "图书"}
    )
    # 打印结果
    for i in range(len(results["ids"][0])):
        print(
            f"   #{i+1} dist={results['distances'][0][i]:.4f} | {results['documents'][0][i]}"
        )

    # TODO ②-3：用户搜索 "户外装备"，只看价格 < 1000 的商品，返回 top-3
    #           提示：where={"price": {"$lt": 1000}}
    query_text = "户外装备"
    query_emb = model.encode([query_text]).tolist()
    results = col.query(
        query_embeddings=query_emb, n_results=3, where={"price": {"$lt": 1000}}
    )
    # 打印结果
    for i in range(len(results["ids"][0])):
        print(
            f"   #{i+1} dist={results['distances'][0][i]:.4f} | {results['documents'][0][i]}"
        )

    # 预期：
    #   "轻便笔记本电脑" 不限类 → #1 MacBook Air (电子产品中最匹配笔记本)
    #   "编程学习书籍" + 图书过滤 → #1 Python编程(最匹配) #2 机器学习实战 #3 设计模式
    #   "户外装备" + 价格<1000 → 过滤掉 >=1000 的商品后检索


# ══════════════════════════════════════════════════════════════
# 任务③ — 修 Bug：Embedding 模型不一致
# ══════════════════════════════════════════════════════════════


def task3_model_mismatch():
    """
    任务目标：发现并修复 ChromaDB 开发中最常见的 bug——
             查询用的 Embedding 模型和入库时用的不一样。

    运行这段代码，观察输出，找出问题所在。
    """

    # 入库时用 all-MiniLM-L6-v2（384维）
    model_en = SentenceTransformer("all-MiniLM-L6-v2")

    client = get_fresh_client()

    # 创建 collection 并存入英文文档
    docs_en = [
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses multiple layers of neural networks",
        "Python is great for data science and ML",
    ]
    metas = [{"lang": "en"} for _ in docs_en]

    col = client.create_collection(name="docs_en")
    col.add(
        embeddings=model_en.encode(docs_en).tolist(),
        documents=docs_en,
        metadatas=metas,
        ids=["en_0", "en_1", "en_2"],
    )
    print(f"\n📦 已入库 {col.count()} 条文档（384维向量）")

    # 查询时不小心用了 multilingual 模型（也是 384 维！）
    # 向量维度相同，所以 ChromaDB 不会报错——但语义空间完全不同
    model_multi = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # TODO ③-1：运行代码，观察两次查询的结果。
    #           第一次用 model_en（正确），第二次用 model_multi（错误）。
    #           虽然维度相同（都是 384），为什么结果会出问题？

    print("\n🔍 查询 1：用 model_en 查询（正确）")
    query = "artificial intelligence"
    q_emb_en = model_en.encode([query]).tolist()
    results_en = col.query(
        query_embeddings=q_emb_en, n_results=3, include=["documents", "distances"]
    )
    for i in range(len(results_en["ids"][0])):
        print(
            f"   #{i+1} dist={results_en['distances'][0][i]:.3f} | {results_en['documents'][0][i]}"
        )

    print("\n🔍 查询 2：用 model_multi 查询（错误 —— 和入库模型不同）")
    q_emb_multi = model_multi.encode([query]).tolist()
    results_multi = col.query(
        query_embeddings=q_emb_multi, n_results=3, include=["documents", "distances"]
    )
    for i in range(len(results_multi["ids"][0])):
        print(
            f"   #{i+1} dist={results_multi['distances'][0][i]:.3f} | {results_multi['documents'][0][i]}"
        )

    # TODO ③-2：对比两次查询的 distances 值。
    #           用错误模型查询时，距离值有什么异常？
    #           为什么 ChromaDB 没有报错？（提示：两个模型维度相同）
    #
    # 你的发现：
    # 使用 model_multi 查询得到的dist值非常大

    # TODO ③-3：这个 bug 在生产环境中怎么避免？
    #           提示：Collection 名、metadata、配置文件
    #
    # 你的建议：
    # metadata写明使用的模型，


# ══════════════════════════════════════════════════════════════
# 任务④ — 扩展场景：性能对比实验
# ══════════════════════════════════════════════════════════════


def task4_performance_comparison():
    """
    任务目标：对比暴力搜索和 ChromaDB 索引搜索在大数据量下的性能差异

    这个任务帮你用数字感受 Step 1 问题中 "10万条时暴力搜索太慢" 具体有多慢。
    """

    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 生成随机"文档"和向量（模拟大量数据，无需真实文本）
    np.random.seed(42)
    num_docs = 5000  # 5000 条数据，避免等待太久
    dim = 384

    print(f"\n🔧 生成 {num_docs} 条随机向量数据...")
    random_vectors = np.random.randn(num_docs, dim).astype(np.float32)
    # 归一化
    random_vectors = random_vectors / np.linalg.norm(
        random_vectors, axis=1, keepdims=True
    )
    docs = [f"document_{i}" for i in range(num_docs)]

    # ══════════════════════════════════════════════════════════
    # Part A：暴力搜索（NumPy 全量计算）
    # ══════════════════════════════════════════════════════════
    print("\n📊 Part A：NumPy 暴力搜索")

    query_vec = random_vectors[0].copy()  # 用第一条数据做查询
    # 加一点噪音，避免查到自己
    query_vec = query_vec + np.random.randn(dim).astype(np.float32) * 0.01
    query_vec = query_vec / np.linalg.norm(query_vec)

    # NumPy 暴力搜索：一次性计算 query 与所有 5000 个向量的余弦相似度
    start = time.perf_counter()
    similarities = np.dot(random_vectors, query_vec)               # (5000,384) × (384,) → (5000,)
    top5_indices = np.argsort(similarities)[::-1][:5]              # 降序取前 5
    top5_scores = similarities[top5_indices]
    elapsed_brute = time.perf_counter() - start

    print(f"   Top-5 相似度: {[f'{s:.4f}' for s in top5_scores]}")
    print(f"   暴力搜索耗时: {elapsed_brute*1000:.2f} ms")

    # ══════════════════════════════════════════════════════════
    # Part B：ChromaDB 索引搜索
    # ══════════════════════════════════════════════════════════
    print("\n📊 Part B：ChromaDB 索引搜索")

    client = get_fresh_client()
    col = client.create_collection(name="perf_test")

    # 批量写入
    print(f"   正在写入 {num_docs} 条向量...")
    batch_size = 1000
    for start_idx in range(0, num_docs, batch_size):
        end_idx = min(start_idx + batch_size, num_docs)
        col.add(
            embeddings=random_vectors[start_idx:end_idx].tolist(),
            documents=docs[start_idx:end_idx],
            ids=[f"d{i}" for i in range(start_idx, end_idx)],
        )

    # 查询
    start = time.perf_counter()
    results = col.query(
        query_embeddings=query_vec.reshape(1, -1).tolist(),
        n_results=5,
    )
    elapsed_chroma = time.perf_counter() - start

    print(f"\n📊 Part B：ChromaDB 索引搜索")
    print(f"   Top-5 结果:")
    for i in range(len(results["ids"][0])):
        print(f"   #{i+1} {results['ids'][0][i]} dist={results['distances'][0][i]:.4f}")
    print(f"   ChromaDB 查询耗时: {elapsed_chroma*1000:.2f} ms")

    # 对比总结
    print(f"\n📊 性能对比：")
    print(f"   NumPy 暴力搜索: {elapsed_brute*1000:.2f} ms  (O(n) = {num_docs} 次计算)")
    print(f"   ChromaDB 索引:   {elapsed_chroma*1000:.2f} ms  (O(log n) ≈ {int(np.log2(num_docs))} 层跳跃)")
    if elapsed_brute > 0:
        speedup = elapsed_brute / elapsed_chroma if elapsed_chroma > 0 else float('inf')
        print(f"   加速比: {speedup:.1f}x")
    print(f"\n   💡 5000 条时暴力搜索反而更快（NumPy 矩阵运算高度优化）。")
    print(f"      想想 100 万条时：")
    print(f"      NumPy 暴力 ≈ {elapsed_brute * 200:.0f} ms（线性 O(n)，×200）")
    print(f"      ChromaDB   ≈ {elapsed_chroma * 3:.0f} ms（对数 O(log n)，仅 ×3）")
    print(f"      → 向量数据库的价值在小数据量时不明显，大规模时不可替代")


# ══════════════════════════════════════════════════════════════
# 任务分发
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请指定任务编号：")
        print("  uv run python code/04-rag/vector-db/step3_tasks.py 1")
        print("  uv run python code/04-rag/vector-db/step3_tasks.py 2")
        print("  uv run python code/04-rag/vector-db/step3_tasks.py 3")
        print("  uv run python code/04-rag/vector-db/step3_tasks.py 4")
        sys.exit(1)

    task_num = sys.argv[1]
    tasks = {
        "1": ("改参数：对比三种距离度量", task1_distance_metrics),
        "2": ("加功能：构建可过滤的产品搜索", task2_filtered_search),
        "3": ("修 Bug：Embedding 模型不一致", task3_model_mismatch),
        "4": ("扩展场景：性能对比实验", task4_performance_comparison),
    }

    if task_num not in tasks:
        print(f"无效任务编号: {task_num}，请输入 1-4")
        sys.exit(1)

    name, func = tasks[task_num]
    print(f"\n{'=' * 60}")
    print(f"  任务{task_num}：{name}")
    print(f"{'=' * 60}")
    func()
    print(f"\n✅ 任务{task_num}完成！")
