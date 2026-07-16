"""
Step 0 — 向量数据库热身运行
目标：直观感受 ChromaDB 的基本操作——存、查、删、过滤
"""

import chromadb
from sentence_transformers import SentenceTransformer


def main():
    # ══════════════════════════════════════════════════════════
    # 第 1 步：创建客户端和 Collection
    # ══════════════════════════════════════════════════════════
    print("=" * 60)
    print("📦 创建 ChromaDB 客户端和 Collection...")
    print()

    # ChromaDB 客户端（数据存到本地磁盘，重启后还在）
    client = chromadb.PersistentClient(path="./chroma_data")

    # 如果之前运行过，先清掉旧数据
    try:
        client.delete_collection("faq_knowledge")
    except Exception:
        pass

    # 创建 Collection——类似关系数据库里的"表"
    # embedding_function 告诉 ChromaDB 用哪个模型把文本转成向量
    collection = client.create_collection(
        name="faq_knowledge",
        metadata={"description": "客服 FAQ 知识库", "version": "1.0"},
    )

    print(f"   Collection 名称: {collection.name}")
    print(f"   Collection 元数据: {collection.metadata}")
    print(f"   当前文档数: {collection.count()}")

    # ══════════════════════════════════════════════════════════
    # 第 2 步：手动生成 Embedding 并添加文档
    # ══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🔢 加载 Embedding 模型，手动生成向量...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # 我们的 FAQ 文档
    documents = [
        "退货政策：自收到商品之日起7天内可申请无理由退货，需保持商品完好。",
        "支付方式：支持微信支付、支付宝、银联卡和信用卡。",
        "国际配送：DHL配送费按重量计算，时效5-10个工作日。",
        "会员积分：每消费1元积1分，100分可抵1元现金。",
        "发票开具：电子发票在订单完成后自动发送至注册邮箱。",
        "账号安全：如发现异常登录，请立即修改密码并联系客服冻结账号。",
    ]

    # 对应的元数据（每个文档的附加信息，用于过滤）
    metadatas = [
        {"category": "退货", "priority": "high"},
        {"category": "支付", "priority": "medium"},
        {"category": "配送", "priority": "medium"},
        {"category": "会员", "priority": "low"},
        {"category": "发票", "priority": "low"},
        {"category": "安全", "priority": "high"},
    ]

    ids = [f"faq_{i}" for i in range(len(documents))]

    # 用模型生成向量
    print("   正在编码文档...")
    embeddings = model.encode(documents).tolist()

    # 存入 ChromaDB
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

    print(f"   ✅ 已添加 {collection.count()} 条文档")
    print(f"   向量维度: {len(embeddings[0])}")

    # ══════════════════════════════════════════════════════════
    # 第 3 步：语义查询
    # ══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🔍 语义查询：")
    print()

    queries = [
        "东西买错了怎么退？",
        "国外运费多少钱？",
    ]

    for query in queries:
        # 查询文本也需要用同一个模型编码
        query_emb = model.encode([query]).tolist()

        # 在 Collection 中搜索最相似的 3 条
        results = collection.query(
            query_embeddings=query_emb,
            n_results=3,
            # include 控制返回哪些字段
            include=["documents", "metadatas", "distances"],
        )

        print(f"   查询: \"{query}\"")
        print(f"   {'─' * 50}")

        # results 的结构：{ids: [[id1,id2,...]], documents: [[doc1,doc2,...]], ...}
        for i in range(len(results["ids"][0])):
            doc_id = results["ids"][0][i]
            doc = results["documents"][0][i]
            dist = results["distances"][0][i]
            meta = results["metadatas"][0][i]
            print(f"   #{i+1} [{doc_id}] 距离={dist:.3f} | 类别={meta['category']}")
            print(f"        \"{doc}\"")
        print()

    # ══════════════════════════════════════════════════════════
    # 第 4 步：带元数据过滤的查询
    # ══════════════════════════════════════════════════════════
    print("=" * 60)
    print("🎯 带元数据过滤的查询（只看 priority=high 的文档）：")
    print()

    query_emb = model.encode(["如何保障账号安全"]).tolist()

    results = collection.query(
        query_embeddings=query_emb,
        n_results=3,
        where={"priority": "high"},  # 只在高优先级文档里检索
        include=["documents", "metadatas", "distances"],
    )

    for i in range(len(results["ids"][0])):
        doc = results["documents"][0][i]
        dist = results["distances"][0][i]
        meta = results["metadatas"][0][i]
        print(f"   #{i+1} 距离={dist:.3f} | 类别={meta['category']} | 优先级={meta['priority']}")
        print(f"        \"{doc}\"")

    # ══════════════════════════════════════════════════════════
    # 第 5 步：查看 Collection 内部
    # ══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("📋 Collection 内部数据一览：")
    print()

    # peek() 类似于 SELECT * LIMIT N
    peek = collection.peek(limit=3)
    print(f"   总文档数: {collection.count()}")
    print(f"   前 3 条 ID: {peek['ids']}")

    # get() 可以按条件取数据
    all_docs = collection.get(include=["metadatas"])
    categories = set(m["category"] for m in all_docs["metadatas"])
    print(f"   所有分类: {categories}")

    print("\n" + "=" * 60)
    print("✅ Step 0 热身完成！")
    print(f"   ChromaDB 数据已持久化到: ./chroma_data/")


if __name__ == "__main__":
    main()
