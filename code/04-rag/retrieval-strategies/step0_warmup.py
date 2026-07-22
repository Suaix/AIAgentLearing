"""
Step 0 — 检索策略热身运行
目标：直观感受 4 种检索策略在同一文档集上的不同表现

策略一览：
  A. Top-K 语义搜索     — 基线：纯向量相似度，取前 K 个
  B. MMR 最大边际相关性  — 在相关性 + 多样性之间找平衡
  C. 混合搜索（Hybrid） — 语义向量 + 关键词匹配，互补增强
  D. 两阶段重排序       — 粗筛（快速）→ 精排（准确），性价比最优
"""

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def normalize_scores(scores: list[float]) -> list[float]:
    """Min-Max 归一化到 [0, 1]"""
    s_min, s_max = min(scores), max(scores)
    if s_max == s_min:
        return [0.5] * len(scores)
    return [(s - s_min) / (s_max - s_min) for s in scores]


def jaccard_keyword_score(query: str, doc: str) -> float:
    """
    基于 Jaccard 系数的关键词匹配分数（轻量级 BM25 替代）

    Jaccard = |Q_words ∩ D_words| / |Q_words ∪ D_words|
    衡量查询词和文档词的集合重叠度，对中文自动分词（按字符 2-gram）
    """
    def tokenize(text: str) -> set[str]:
        # 简单 2-gram 分词（跳过纯空格和标点）
        chars = [c for c in text if c not in "，。！？；：、\"'（）\n "]
        bigrams = {chars[i] + chars[i+1] for i in range(len(chars) - 1)}
        # 也加入单字（处理短查询）
        unigrams = set(chars)
        return bigrams | unigrams

    q_tokens = tokenize(query)
    d_tokens = tokenize(doc)

    if not q_tokens or not d_tokens:
        return 0.0

    intersection = q_tokens & d_tokens
    union = q_tokens | d_tokens
    return len(intersection) / len(union)


def mmr_select(
    query_emb: np.ndarray,
    doc_embs: list[np.ndarray],
    docs: list[str],
    top_k: int = 3,
    lambda_param: float = 0.7,
) -> list[tuple[int, str, float]]:
    """
    MMR (Maximal Marginal Relevance) 贪心选择

    每轮选择最大化以下目标函数的文档：
      λ × sim(D_i, Q) — (1-λ) × max_{已选 D_j} sim(D_i, D_j)

    λ=1.0 → 纯相关性（退化为 Top-K）
    λ=0.0 → 纯多样性
    λ=0.7 → 推荐默认值：偏相关性，但惩罚与已选内容相似的文档

    参数：
        lambda_param: 相关性权重（0-1），越大越偏相关性
    """
    n = len(docs)
    selected = []
    remaining = list(range(n))

    # 预计算所有文档间相似度（避免重复计算）
    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            s = cosine_similarity(doc_embs[i], doc_embs[j])
            sim_matrix[i][j] = s
            sim_matrix[j][i] = s

    # 查询-文档相似度
    query_sims = np.array([cosine_similarity(query_emb, doc_embs[i]) for i in range(n)])

    for _ in range(min(top_k, n)):
        best_idx = -1
        best_score = -float("inf")

        for idx in remaining:
            relevance = query_sims[idx]

            # 与已选文档的最大相似度（多样性惩罚项）
            diversity_penalty = 0.0
            if selected:
                diversity_penalty = max(sim_matrix[idx][s] for s in selected)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx == -1:
            break

        selected.append(best_idx)
        remaining.remove(best_idx)

    return [(i, docs[i], query_sims[i]) for i in selected]


def main():
    np.random.seed(42)

    # ══════════════════════════════════════════════════════════
    # 第 1 步：准备文档集合
    # ══════════════════════════════════════════════════════════
    print("=" * 70)
    print("📚 文档集合（电商客服 FAQ 知识库）：")
    print("=" * 70)

    documents = [
        "退货政策：自收到商品之日起7天内可申请无理由退货，需保持商品完好无损，附带原包装。退回运费由买家承担。",
        "换货流程：若商品存在质量问题，可在收到后15天内申请换货。需提供商品瑕疵照片，审核通过后发新货。",
        "支付方式：支持微信支付、支付宝、银联卡和信用卡。大额订单支持分期付款，3期免息。",
        "退款时效：审核通过后，微信/支付宝退款1-3个工作日到账；银行卡退款3-7个工作日到账。",
        "国际配送：DHL配送费按重量计算，0-1kg收取80元，1-3kg收取150元，时效5-10个工作日。",
        "国内配送：顺丰包邮，下单后24小时内发货，全国1-3天送达。偏远地区加收20元。",
        "会员积分：每消费1元积1分，100分可抵1元现金。生日当月双倍积分，积分有效期12个月。",
        "会员等级：银卡会员9.8折、金卡会员9.5折、钻石会员9折。等级按年消费金额评定。",
        "发票开具：电子发票在订单完成后自动发送至注册邮箱。企业发票需提前填写税号信息。",
        "账号安全：如发现异常登录，请立即修改密码并联系客服冻结账号。建议开启两步验证。",
    ]

    for i, doc in enumerate(documents):
        cat = doc.split("：")[0]
        print(f"  [{i}] ({cat}) {doc[:60]}...")

    print(f"\n  共 {len(documents)} 篇文档\n")

    # ══════════════════════════════════════════════════════════
    # 第 2 步：加载模型，预计算所有文档向量
    # ══════════════════════════════════════════════════════════
    print("=" * 70)
    print("🔢 加载模型并编码文档...")

    # 双编码器（Bi-Encoder）：用于语义搜索，速度快
    bi_encoder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    doc_embeddings = [bi_encoder.encode(doc) for doc in documents]

    # 交叉编码器（Cross-Encoder）：用于重排序，更准确但更慢
    # 它同时接收 (query, doc) 对，输出相关性分数
    print("   加载交叉编码器（用于策略D重排序）...")
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    print(f"   双编码器向量维度: {len(doc_embeddings[0])}")
    print(f"   文档数: {len(documents)}\n")

    # ══════════════════════════════════════════════════════════
    # 第 3 步：4 种检索策略对比
    # ══════════════════════════════════════════════════════════
    print("=" * 70)
    print("🔍 检索策略对比")
    print("=" * 70)

    queries = [
        "我买的东西怎么退？",
        "运费要多少钱？",
        "会员有什么优惠？",
    ]

    for q_idx, query in enumerate(queries):
        print(f"\n{'─' * 70}")
        print(f"\n📝 查询 {q_idx+1}: \"{query}\"")
        print()

        query_emb = bi_encoder.encode(query)

        # ────────────────────────────────────────────────
        # 策略 A：Top-K 语义搜索（基线）
        # ────────────────────────────────────────────────
        print("  ┌─ 策略A：Top-K 语义搜索 ─────────────────────────────")
        semantic_scores = [cosine_similarity(query_emb, doc_embeddings[i]) for i in range(len(documents))]
        top_k_indices = np.argsort(semantic_scores)[::-1][:3]

        for rank, idx in enumerate(top_k_indices):
            cat = documents[idx].split("：")[0]
            print(f"  │ #{rank+1} [{idx}] {cat} (相似度: {semantic_scores[idx]:.3f})")
            print(f"  │    \"{documents[idx][:80]}...\"")
        print("  └──────────────────────────────────────────────────")

        # ────────────────────────────────────────────────
        # 策略 B：MMR 多样性检索
        # ────────────────────────────────────────────────
        print()
        print("  ┌─ 策略B：MMR (λ=0.7) 多样性检索 ──────────────────")
        print("  │  λ=0.7 → 偏相关性，同时惩罚内容相似的文档")
        mmr_results = mmr_select(query_emb, doc_embeddings, documents, top_k=3, lambda_param=0.7)

        for rank, (idx, doc, sim) in enumerate(mmr_results):
            cat = doc.split("：")[0]
            print(f"  │ #{rank+1} [{idx}] {cat} (语义相似度: {sim:.3f})")
            print(f"  │    \"{doc[:80]}...\"")
        print("  └──────────────────────────────────────────────────")

        # ────────────────────────────────────────────────
        # 策略 C：混合搜索（语义 + 关键词）
        # ────────────────────────────────────────────────
        print()
        print("  ┌─ 策略C：混合搜索 (α=0.6 语义 + 0.4 关键词) ──────")

        alpha = 0.6  # 语义权重
        # 归一化两种分数
        norm_semantic = normalize_scores(semantic_scores)
        kw_scores = [jaccard_keyword_score(query, doc) for doc in documents]
        norm_kw = normalize_scores(kw_scores)

        hybrid_scores = [alpha * norm_semantic[i] + (1 - alpha) * norm_kw[i] for i in range(len(documents))]
        hybrid_indices = np.argsort(hybrid_scores)[::-1][:3]

        for rank, idx in enumerate(hybrid_indices):
            cat = documents[idx].split("：")[0]
            print(f"  │ #{rank+1} [{idx}] {cat} (语义:{norm_semantic[idx]:.2f} + 关键词:{norm_kw[idx]:.2f} = 综合:{hybrid_scores[idx]:.2f})")
            print(f"  │    \"{documents[idx][:80]}...\"")
        print("  └──────────────────────────────────────────────────")

        # ────────────────────────────────────────────────
        # 策略 D：两阶段重排序（粗筛 → 精排）
        # ────────────────────────────────────────────────
        print()
        print("  ┌─ 策略D：两阶段重排序 ────────────────────────────")

        # 第一阶段：语义搜索粗筛，取 top-2K（这里 K=3，所以取 2*3=6）
        recall_k = min(6, len(documents))
        top_recall_indices = np.argsort(semantic_scores)[::-1][:recall_k]

        print(f"  │ 第一阶段（粗筛）：语义搜索 Top-{recall_k}")
        for rank, idx in enumerate(top_recall_indices):
            cat = documents[idx].split("：")[0]
            print(f"  │   候选#{rank+1} [{idx}] {cat} (相似度: {semantic_scores[idx]:.3f})")

        # 第二阶段：Cross-Encoder 精排
        print(f"  │")
        print(f"  │ 第二阶段（精排）：Cross-Encoder 重排序")
        pairs = [(query, documents[idx]) for idx in top_recall_indices]
        ce_scores = cross_encoder.predict(pairs)

        # 按 CE 分数重排
        reranked = sorted(
            zip(top_recall_indices, ce_scores),
            key=lambda x: x[1], reverse=True
        )[:3]

        for rank, (idx, ce_score) in enumerate(reranked):
            cat = documents[idx].split("：")[0]
            print(f"  │ #{rank+1} [{idx}] {cat} (CE重排分: {ce_score:.3f}, 原相似度: {semantic_scores[idx]:.3f})")
            print(f"  │    \"{documents[idx][:80]}...\"")
        print("  └──────────────────────────────────────────────────")

    # ══════════════════════════════════════════════════════════
    # 第 4 步：策略总结
    # ══════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("📊 四种策略对比总结")
    print("=" * 70)
    print("""
    ┌────────────┬──────────┬──────────┬────────────────────────────┐
    │ 策略       │ 延迟     │ 准确度   │ 适用场景                    │
    ├────────────┼──────────┼──────────┼────────────────────────────┤
    │ A. Top-K   │ ⚡ 极快   │ ★★★     │ 简单问答，结果间不要求多样性  │
    │ B. MMR     │ ⚡ 快     │ ★★★☆    │ 推荐系统、探索式搜索          │
    │ C. Hybrid  │ ⚡ 快     │ ★★★★    │ 有精确术语/实体名的专业领域   │
    │ D. Rerank  │ 🐢 较慢   │ ★★★★★   │ 高精度问答，法律/医疗等场景   │
    └────────────┴──────────┴──────────┴────────────────────────────┘

    💡 关键洞察：
    - Top-K 可能返回 3 条都是"退货"的文档（冗余）
    - MMR 会故意选不同子主题的文档（退货 + 配送 + 支付）
    - Hybrid 能捕捉纯语义搜索漏掉的关键词精确匹配
    - Rerank 用"慢但准"的模型修正"快但粗"的模型排序
    - 生产环境常用 D 的两阶段思路：向量库粗筛 + CE 精排
    """)

    print("✅ Step 0 热身完成！")


if __name__ == "__main__":
    main()
