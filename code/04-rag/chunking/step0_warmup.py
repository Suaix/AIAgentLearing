"""
Step 0 — 文档分块热身运行
目标：直观感受不同分块策略对检索结果的巨大影响
"""

from sentence_transformers import SentenceTransformer
import numpy as np


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def main():
    # ══════════════════════════════════════════════════════════
    # 第 1 步：准备一篇长文档
    # ══════════════════════════════════════════════════════════
    print("=" * 60)
    print("📄 原始文档（一篇关于 Python 和机器学习的文章）：")
    print("=" * 60)

    full_article = """Python 是一种广泛使用的编程语言，以其简洁的语法和丰富的库生态系统而闻名。
在数据科学领域，Python 是最主流的语言之一，拥有 NumPy、Pandas、Matplotlib 等核心库。

机器学习是人工智能的一个子领域，它使计算机能够从数据中学习模式，而无需显式编程。
常见的机器学习算法包括线性回归、决策树、随机森林、支持向量机和神经网络。

深度学习是机器学习的一个分支，使用多层神经网络来学习数据的层次化表示。
PyTorch 和 TensorFlow 是两个最流行的深度学习框架，都提供 Python API。

自然语言处理（NLP）是 AI 的另一个重要领域，专注于让计算机理解和生成人类语言。
现代 NLP 技术包括 Transformer 架构、BERT 预训练模型和大语言模型（LLM）。

在生产环境中部署机器学习模型需要考虑模型版本管理、性能监控、A/B 测试和持续集成。
MLOps 是一套将 DevOps 实践应用于机器学习工作流的工程方法。

RAG（检索增强生成）是一种将信息检索与文本生成相结合的技术，
它先从知识库中检索相关文档片段，再让 LLM 基于这些片段生成更准确的回答。"""

    print(full_article)
    print(f"\n   文章总字数: {len(full_article)} 字")

    # ══════════════════════════════════════════════════════════
    # 第 2 步：三种分块策略
    # ══════════════════════════════════════════════════════════
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # 策略 A：整篇文章一个块（不分块）
    chunks_whole = [full_article]

    # 策略 B：固定大小分块 — 按句子切，每 2 句一块
    sentences = [s.strip() for s in full_article.replace("\n", "").split("。") if s.strip()]
    chunk_size = 2
    chunks_fixed = [
        "。".join(sentences[i:i + chunk_size]) + "。"
        for i in range(0, len(sentences), chunk_size)
    ]

    # 策略 C：滑动窗口分块 — 每 2 句一块，窗口重叠 1 句
    chunks_sliding = [
        "。".join(sentences[i:i + chunk_size]) + "。"
        for i in range(0, len(sentences) - 1)  # -1 确保最后一组也凑齐
    ]

    for name, chunks in [("策略A：整篇不分块", chunks_whole),
                          ("策略B：固定大小（2句/块）", chunks_fixed),
                          ("策略C：滑动窗口（2句/块，重叠1句）", chunks_sliding)]:
        print(f"\n{'─' * 60}")
        print(f"📦 {name} — 共 {len(chunks)} 块")
        for i, chunk in enumerate(chunks):
            print(f"   [{i}] ({len(chunk)}字) {chunk[:80]}...")

        embeddings = model.encode(chunks)
        print(f"   向量矩阵: {embeddings.shape}")

    # ══════════════════════════════════════════════════════════
    # 第 3 步：对比检索效果
    # ══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🔍 检索对比：同一个查询，不同分块策略的效果")
    print("=" * 60)

    queries = [
        "深度学习框架有哪些？",
        "如何部署机器学习模型？",
        "什么是 RAG？",
    ]

    for query in queries:
        print(f"\n{'─' * 60}")
        print(f"🔎 查询: \"{query}\"")

        query_emb = model.encode([query])[0]

        for strategy_name, chunks in [
            ("整篇不分块", chunks_whole),
            ("固定分块 2句/块", chunks_fixed),
            ("滑动窗口 2句/块", chunks_sliding),
        ]:
            embeddings = model.encode(chunks)
            scores = [(i, cosine_similarity(query_emb, embeddings[i]), chunks[i])
                      for i in range(len(chunks))]
            scores.sort(key=lambda x: x[1], reverse=True)

            top = scores[0]
            print(f"\n   [{strategy_name}] Top-1 相似度={top[1]:.3f}")
            print(f"      块[{top[0]}]: \"{top[2][:100]}...\"")

    # ══════════════════════════════════════════════════════════
    # 第 4 步：可视化分块"精度"
    # ══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("📐 信息密度对比：")
    print("=" * 60)

    # 模拟"整篇 vs 分块"的信息稀释效应
    print(f"\n   整篇不分块（{len(full_article)}字）：")
    print(f"     → 查询\"RAG\"时，相关句子只占全文的 10%")
    print(f"     → 其余 90% 内容都是噪声，稀释了相似度分数")

    print(f"\n   固定分块（每块约 {sum(len(c) for c in chunks_fixed)//len(chunks_fixed)} 字）：")
    print(f"     → 查询\"RAG\"时，最匹配的块 90% 内容相关")
    print(f"     → 高信噪比，排名准确")

    print("\n" + "=" * 60)
    print("✅ Step 0 热身完成！")


if __name__ == "__main__":
    main()
