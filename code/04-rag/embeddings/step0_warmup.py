"""
Step 0 — Embedding 热身运行
目标：直观感受"文本 → 向量 → 相似度计算"
"""

import numpy as np
from sentence_transformers import SentenceTransformer


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def main():
    # ──────────────────────────────────────────
    # 第 1 步：加载模型
    # ──────────────────────────────────────────
    print("=" * 60)
    print("📦 加载 Embedding 模型...")
    # all-MiniLM-L6-v2：轻量级英文模型，384 维向量，~80MB
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"   模型维度: {model.get_sentence_embedding_dimension()}")
    print(f"   最大序列长度: {model.max_seq_length}")

    # ──────────────────────────────────────────
    # 第 2 步：将文本转换为向量（Embedding）
    # ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🔢 将文本转换为向量...")

    sentences = [
        "The cat sits on the mat",              # ① 猫在垫子上
        "A feline is resting on a rug",         # ② 猫科动物在地毯上休息
        "I love programming in Python",         # ③ 我喜欢 Python 编程
        "Software engineering is my passion",   # ④ 软件工程是我的热情
        "The weather is nice today",            # ⑤ 今天天气不错
        "It is sunny and warm outside",         # ⑥ 外面阳光明媚又温暖
    ]

    embeddings = model.encode(sentences)

    for i, (text, emb) in enumerate(zip(sentences, embeddings)):
        print(f"\n   [{i}] {text}")
        print(f"       向量维度: {len(emb)}")
        print(f"       前 5 个值: {emb[:5]}")

    # ──────────────────────────────────────────
    # 第 3 步：计算相似度矩阵
    # ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 余弦相似度矩阵（6 × 6）：")
    print()

    # 打印表头
    header = "        " + "  ".join(f"[{i}]" for i in range(6))
    print(header)
    print("       " + "-" * 35)

    for i in range(6):
        row = f"  [{i}] |"
        for j in range(6):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            row += f" {sim:.2f}"
        print(row)

    # ──────────────────────────────────────────
    # 第 4 步：语义搜索演示
    # ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🔍 语义搜索演示：")
    print()

    query = "Coding and software development"
    query_emb = model.encode([query])[0]

    print(f"   查询: \"{query}\"")
    print(f"\n   相似度排名:")
    print(f"   {'─' * 45}")

    # 计算每个句子与查询的相似度，排序
    scores = [(i, cosine_similarity(query_emb, embeddings[i]), sentences[i])
              for i in range(6)]
    scores.sort(key=lambda x: x[1], reverse=True)

    for rank, (idx, score, text) in enumerate(scores, 1):
        bar = "█" * int(score * 20)
        print(f"   #{rank} [{idx}] 相似度={score:.3f} {bar}")
        print(f"        \"{text}\"")
        print()

    # ──────────────────────────────────────────
    # 第 5 步：跨语言相似度（可选观察）
    # ──────────────────────────────────────────
    print("=" * 60)
    print("🌍 额外观察 — 中英文语义相似度：")
    print()

    en_text = "Machine learning is transforming the world"
    zh_text = "机器学习正在改变世界"

    en_emb = model.encode([en_text])[0]
    zh_emb = model.encode([zh_text])[0]

    sim = cosine_similarity(en_emb, zh_emb)
    print(f"   英文: \"{en_text}\"")
    print(f"   中文: \"{zh_text}\"")
    print(f"   相似度: {sim:.3f}")
    print(f"   → {'✅ 模型能识别跨语言语义相似性' if sim > 0.5 else '⚠️ 该模型对中文支持有限'}")

    print("\n" + "=" * 60)
    print("✅ Step 0 热身完成！")


if __name__ == "__main__":
    main()
