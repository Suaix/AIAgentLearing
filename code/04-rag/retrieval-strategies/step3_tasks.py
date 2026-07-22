"""
Step 3 — 检索策略：引导式修改任务

四个任务通过命令行参数选择：
  uv run python code/04-rag/retrieval-strategies/step3_tasks.py 1   # 改参数：MMR λ 实验
  uv run python code/04-rag/retrieval-strategies/step3_tasks.py 2   # 加功能：实现 RRF 融合
  uv run python code/04-rag/retrieval-strategies/step3_tasks.py 3   # 修Bug：MMR 公式权重颠倒
  uv run python code/04-rag/retrieval-strategies/step3_tasks.py 4   # 扩展：查询扩展（Query Expansion）
"""

import numpy as np
from regex import T
from sentence_transformers import SentenceTransformer, CrossEncoder
import sys

# ═══════════════════════════════════════════════════════════════
# 共享工具函数（已实现，无需修改）
# ═══════════════════════════════════════════════════════════════

DOCUMENTS = [
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

QUERIES = [
    "我买的东西怎么退？",
    "运费要多少钱？",
    "会员有什么优惠？",
]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def jaccard_keyword_score(query: str, doc: str) -> float:
    """基于 Jaccard 系数的关键词匹配分数"""

    def tokenize(text: str) -> set[str]:
        chars = [c for c in text if c not in "，。！？；：、\"'（）\n "]
        bigrams = {chars[i] + chars[i + 1] for i in range(len(chars) - 1)}
        return bigrams | set(chars)

    q_tokens = tokenize(query)
    d_tokens = tokenize(doc)
    if not q_tokens or not d_tokens:
        return 0.0
    intersection = q_tokens & d_tokens
    union = q_tokens | d_tokens
    return len(intersection) / len(union)


def normalize_scores(scores: list[float]) -> list[float]:
    """Min-Max 归一化到 [0, 1]"""
    s_min, s_max = min(scores), max(scores)
    if s_max == s_min:
        return [0.5] * len(scores)
    return [(s - s_min) / (s_max - s_min) for s in scores]


def mmr_select(
    query_emb: np.ndarray,
    doc_embs: list[np.ndarray],
    docs: list[str],
    top_k: int = 3,
    lambda_param: float = 0.7,
) -> list[tuple[int, str, float]]:
    """
    MMR (Maximal Marginal Relevance) 贪心选择
    lambda_param: 相关性权重（0-1），越大越偏相关性
    """
    n = len(docs)
    selected = []
    remaining = list(range(n))

    # 预计算文档间相似度矩阵
    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            s = cosine_similarity(doc_embs[i], doc_embs[j])
            sim_matrix[i][j] = s
            sim_matrix[j][i] = s

    query_sims = np.array([cosine_similarity(query_emb, doc_embs[i]) for i in range(n)])

    for _ in range(min(top_k, n)):
        best_idx = -1
        best_score = -float("inf")

        for idx in remaining:
            relevance = query_sims[idx]
            diversity_penalty = 0.0
            if selected:
                diversity_penalty = max(sim_matrix[idx][s] for s in selected)

            mmr_score = (
                lambda_param * relevance - (1 - lambda_param) * diversity_penalty
            )

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx == -1:
            break

        selected.append(best_idx)
        remaining.remove(best_idx)

    return [(i, docs[i], query_sims[i]) for i in selected]


def get_model():
    """懒加载模型（避免重复加载）"""
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


# ═══════════════════════════════════════════════════════════════
# 任务 ①：改参数 — 实验 MMR 的 λ 参数
# ═══════════════════════════════════════════════════════════════


def task1():
    """
    目标：实验 MMR 的 λ 参数对检索结果的影响。

    λ 控制"相关性 vs 多样性"的权衡：
      λ=1.0 → 只关心相关性（退化为 Top-K）
      λ=0.0 → 只关心多样性（第一选随机，后续选和前面最不相似的）
      λ=0.7 → 默认推荐值

    任务步骤：
      1. 运行当前代码，观察四个 λ 值下同一条查询的结果排序
      2. 回答代码末尾的问题

    运行：uv run python code/04-rag/retrieval-strategies/step3_tasks.py 1
    """
    model = get_model()
    doc_embeddings = [model.encode(doc) for doc in DOCUMENTS]

    query = "我买的东西怎么退？"
    query_emb = model.encode(query)

    lambda_values = [0.3, 0.5, 0.7, 0.9]

    print("=" * 65)
    print(f"任务 ①：MMR λ 参数实验")
    print(f'查询: "{query}"')
    print("=" * 65)

    semantic_scores = [
        cosine_similarity(query_emb, doc_embeddings[i]) for i in range(len(DOCUMENTS))
    ]
    top_k_indices = np.argsort(semantic_scores)[::-1][:3]

    print(f"\n📌 基线：纯 Top-K 语义搜索（无多样性控制）")
    for rank, idx in enumerate(top_k_indices):
        print(
            f"   #{rank+1} [{idx}] {DOCUMENTS[idx].split('：')[0]} (相似度={semantic_scores[idx]:.3f})"
        )

    for lam in lambda_values:
        print(f"\n{'─' * 50}")
        print(
            f"🔧 MMR λ={lam} ({'偏多样性' if lam < 0.5 else '均衡' if lam == 0.5 else '偏相关性'})"
        )
        results = mmr_select(
            query_emb, doc_embeddings, DOCUMENTS, top_k=3, lambda_param=lam
        )

        for rank, (idx, doc, sim) in enumerate(results):
            cat = doc.split("：")[0]
            print(f"   #{rank+1} [{idx}] {cat} (相关度={sim:.3f})")

    # TODO: 观察输出，回答以下问题
    print(f"\n{'=' * 65}")
    print("📝 请回答（在代码中填写或口头回答）：")
    print("   Q1: λ=0.3 时，#2 返回的是哪个文档？和 Top-K 的 #2 有什么不同？")
    print("   Q2: λ=0.9 时结果几乎等价于 Top-K，为什么？")
    print("   Q3: 如果你的产品是做'猜你喜欢'推荐，你会选大 λ 还是小 λ？为什么？")
    # Q1: 返回的是“账号安全“文档，与Top-K的“换货流程“不一样，与退货的主题也不一样。
    # Q2：λ=0.9 时相同主题惩罚性低，结果跟Top-K几乎等价。
    # Q3：小λ，保持主题多样性，覆盖面更换。


# ═══════════════════════════════════════════════════════════════
# 任务 ②：加功能 — 实现 RRF (Reciprocal Rank Fusion)
# ═══════════════════════════════════════════════════════════════


def reciprocal_rank_fusion(
    semantic_ranking: list[int],
    keyword_ranking: list[int],
    k: int = 60,
) -> list[tuple[int, float]]:
    """
    RRF (Reciprocal Rank Fusion) — 融合多个排序列表

    公式：RRF_score(d) = Σ 1 / (k + rank_i(d))

    其中：
      rank_i(d) 是文档 d 在第 i 个排序列表中的排名（从 1 开始）
      k 是平滑常数（默认 60），防止 1/rank 在排名差异小时过度敏感

    与 Step 0 中"归一化分数再加权"的方法不同，RRF 不关心原始分数大小，
    只关心相对排名——这在 Combining results from heterogeneous sources
    （如语义搜索 + BM25 + 点击率）时非常有用。

    参数：
        semantic_ranking: 语义搜索返回的文档索引列表（按相关度降序）
        keyword_ranking:  关键词搜索返回的文档索引列表（按相关度降序）
        k: 平滑常数

    返回：
        [(doc_idx, rrf_score), ...] 按 RRF 分数降序排列

    参考资料：https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf

    API 提示：
      - semantic_ranking.index(doc_idx) 可以得到 doc_idx 在列表中的位置
      - 排名从 1 开始（不是从 0 开始）→ rank = index + 1
      - 两个列表长度可能不同——只出现在其中一个列表中的文档，在另一个列表中排名 = len(list) + 1
    """
    # TODO: 实现 RRF 算法
    # 步骤：
    #   1. 收集所有出现过的 doc_idx（两个列表的并集）
    #   2. 对每个 doc_idx，计算在两个列表中的排名
    #   3. 用 RRF 公式计算融合分数
    #   4. 按 RRF 分数降序排列，返回 [(doc_idx, rrf_score), ...]
    doc_idxs = list(set(semantic_ranking + keyword_ranking))
    result = []
    for doc_id in doc_idxs:
        rank1 = (
            semantic_ranking.index(doc_id) + 1
            if doc_id in semantic_ranking
            else len(semantic_ranking) + 1
        )
        rank2 = (
            keyword_ranking.index(doc_id) + 1
            if doc_id in keyword_ranking
            else len(keyword_ranking) + 1
        )
        rrf_score = 1 / (k + rank1) + 1 / (k + rank2)
        result.append((doc_id, rrf_score))

    result.sort(key=lambda x: x[1], reverse=True)
    return result


def task2():
    """
    目标：实现 RRF 融合算法，替代 Step 0 中简单的分数归一化 + 加权。

    运行：uv run python code/04-rag/retrieval-strategies/step3_tasks.py 2
    """
    model = get_model()
    doc_embeddings = [model.encode(doc) for doc in DOCUMENTS]

    query = "运费要多少钱？"
    query_emb = model.encode(query)

    # 构建两个独立的排序列表
    semantic_scores = [
        cosine_similarity(query_emb, doc_embeddings[i]) for i in range(len(DOCUMENTS))
    ]
    keyword_scores = [jaccard_keyword_score(query, doc) for doc in DOCUMENTS]

    semantic_ranking = [int(i) for i in np.argsort(semantic_scores)[::-1]]
    keyword_ranking = [int(i) for i in np.argsort(keyword_scores)[::-1]]

    print("=" * 65)
    print("任务 ②：RRF 融合")
    print(f'查询: "{query}"')
    print("=" * 65)

    print(f"\n📌 语义搜索排序: {semantic_ranking}")
    print(
        f"   (分数: {[f'{semantic_scores[i]:.3f}' for i in semantic_ranking[:5]]}...)"
    )
    print(f"\n📌 关键词搜索排序: {keyword_ranking}")
    print(f"   (分数: {[f'{keyword_scores[i]:.3f}' for i in keyword_ranking[:5]]}...)")

    # 调用 RRF
    rrf_results = reciprocal_rank_fusion(semantic_ranking, keyword_ranking)
    # 注意：上面函数实现完成后，下行才能正常输出

    if rrf_results:
        print(f"\n✅ RRF 融合结果（Top-3）：")
        for rank, (idx, score) in enumerate(rrf_results[:3]):
            cat = DOCUMENTS[idx].split("：")[0]
            sem_rank = semantic_ranking.index(idx) + 1
            kw_rank = keyword_ranking.index(idx) + 1
            print(f"   #{rank+1} [{idx}] {cat}")
            print(
                f"        RRF={score:.4f} | 语义排名={sem_rank} | 关键词排名={kw_rank}"
            )
    else:
        print("\n⚠️  RRF 函数尚未实现，请完成 reciprocal_rank_fusion() 后再运行。")

    # 对比：Step 0 的加权求和方式
    print(f"\n📊 对比：Step 0 归一化+加权 (α=0.6)")
    norm_sem = normalize_scores(semantic_scores)
    norm_kw = normalize_scores(keyword_scores)
    hybrid_scores = [
        0.6 * norm_sem[i] + 0.4 * norm_kw[i] for i in range(len(DOCUMENTS))
    ]
    hybrid_ranking = np.argsort(hybrid_scores)[::-1][:3]
    for rank, idx in enumerate(hybrid_ranking):
        cat = DOCUMENTS[idx].split("：")[0]
        print(f"   #{rank+1} [{idx}] {cat} (综合={hybrid_scores[idx]:.2f})")


# ═══════════════════════════════════════════════════════════════
# 任务 ③：修Bug — MMR 公式中 λ 权重被反转
# ═══════════════════════════════════════════════════════════════


def mmr_select_buggy(
    query_emb: np.ndarray,
    doc_embs: list[np.ndarray],
    docs: list[str],
    top_k: int = 3,
    lambda_param: float = 0.7,
) -> list[tuple[int, str, float]]:
    """
    MMR — 有 bug 的版本。

    预期行为：λ=0.9 时应该非常接近 Top-K（强调相关性）
    实际行为：λ=0.9 时结果反而更加"分散"，和 Top-K 差异很大
              λ=0.1 时反而接近 Top-K

    提示：观察 mmr_score 的计算公式，找到 λ 和 (1-λ) 哪个加在了相关性上。
    """
    n = len(docs)
    selected = []
    remaining = list(range(n))

    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            s = cosine_similarity(doc_embs[i], doc_embs[j])
            sim_matrix[i][j] = s
            sim_matrix[j][i] = s

    query_sims = np.array([cosine_similarity(query_emb, doc_embs[i]) for i in range(n)])

    for _ in range(min(top_k, n)):
        best_idx = -1
        best_score = -float("inf")

        for idx in remaining:
            relevance = query_sims[idx]
            diversity_penalty = 0.0
            if selected:
                diversity_penalty = max(sim_matrix[idx][s] for s in selected)

            # ═══════════════════════════════════════════════════
            # BUG 在这里：λ 和 (1-λ) 的位置反了！
            # 预期：λ × relevance − (1-λ) × diversity
            # 当前：(1-λ) × relevance − λ × diversity ← 权重颠倒
            mmr_score = (lambda_param) * relevance - (
                1 - lambda_param
            ) * diversity_penalty
            # TODO: 修复上面这行 —— 把 λ 换到正确的位置
            # ═══════════════════════════════════════════════════

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx == -1:
            break

        selected.append(best_idx)
        remaining.remove(best_idx)

    return [(i, docs[i], query_sims[i]) for i in selected]


def task3():
    """
    目标：找到并修复 mmr_select_buggy() 中 λ 权重反转的 bug。

    调试思路：
      1. 运行当前代码，观察 λ=0.9 时的输出
      2. 对比 λ=0.9 和 Top-K —— 预期应该非常接近，但实际差很远
      3. 再观察 λ=0.1 —— 预期应该很分散，但实际接近 Top-K
      4. 找到 mmr_score 的计算公式，检查 λ 的位置

    运行：uv run python code/04-rag/retrieval-strategies/step3_tasks.py 3
    """
    model = get_model()
    doc_embeddings = [model.encode(doc) for doc in DOCUMENTS]

    query = "我买的东西怎么退？"
    query_emb = model.encode(query)

    print("=" * 65)
    print("任务 ③：修Bug — MMR 公式权重反转")
    print(f'查询: "{query}"')
    print("=" * 65)

    # 基线：Top-K
    semantic_scores = [
        cosine_similarity(query_emb, doc_embeddings[i]) for i in range(len(DOCUMENTS))
    ]
    top_k_indices = np.argsort(semantic_scores)[::-1][:3]
    print(
        f"\n📌 Top-K 基线：{[f'[{i}]{DOCUMENTS[i].split(chr(58))[0]}' for i in top_k_indices]}"
    )

    # Buggy MMR（λ=0.9 应该接近 Top-K，但现在不是）
    print(f"\n⚠️  Buggy MMR λ=0.9（预期接近 Top-K）：")
    results_bug = mmr_select_buggy(
        query_emb, doc_embeddings, DOCUMENTS, top_k=3, lambda_param=0.9
    )
    for rank, (idx, doc, sim) in enumerate(results_bug):
        print(f"   #{rank+1} [{idx}] {doc.split('：')[0]} (相关度={sim:.3f})")

    print(f"\n⚠️  Buggy MMR λ=0.1（预期非常分散）：")
    results_bug2 = mmr_select_buggy(
        query_emb, doc_embeddings, DOCUMENTS, top_k=3, lambda_param=0.1
    )
    for rank, (idx, doc, sim) in enumerate(results_bug2):
        print(f"   #{rank+1} [{idx}] {doc.split('：')[0]} (相关度={sim:.3f})")

    # 正确版本对比
    print(f"\n✅ 正确 MMR λ=0.9（参考）：")
    results_correct = mmr_select(
        query_emb, doc_embeddings, DOCUMENTS, top_k=3, lambda_param=0.9
    )
    for rank, (idx, doc, sim) in enumerate(results_correct):
        print(f"   #{rank+1} [{idx}] {doc.split('：')[0]} (相关度={sim:.3f})")

    print(
        f"\n📝 找到 bug 后，修改 mmr_select_buggy() 中标注了 BUG 的那行代码，重新运行验证。"
    )


# ═══════════════════════════════════════════════════════════════
# 任务 ④：扩展 — 查询扩展（Query Expansion）
# ═══════════════════════════════════════════════════════════════


def expand_query(
    query: str,
    initial_results: list[str],
    top_n_terms: int = 3,
) -> str:
    """
    查询扩展：用初次检索到的文档中的关键词扩充原始查询。

    算法思路（PRF — Pseudo Relevance Feedback 的简化版）：
      1. 假设 Top-K 检索结果是"相关"的（伪相关反馈）
      2. 从这些文档中提取高频关键词（用 TF-IDF 或简单词频）
      3. 将 Top-N 个关键词追加到原始查询中

    示例：
      原查询: "怎么退"
      检索到的文档包含: "退货政策"、"退款时效"、"7天内"
      扩展后: "怎么退 退货政策 退款 时效"

    参数：
        query: 原始查询字符串
        initial_results: 初次检索返回的相关文档列表
        top_n_terms: 提取的关键词数量

    返回：
        扩展后的查询字符串

    API 提示：
      - 用 jaccard_keyword_score 或简单的词频统计来识别关键词
      - 从 initial_results 的所有文档中提取出现频率最高的 top_n_terms 个词
      - 把这些词追加到 query 后面
    """

    # TODO: 实现查询扩展
    # 步骤：
    #   1. 对 initial_results 中的每个文档做分词（复用 jaccard_keyword_score 里的 tokenize）
    #   2. 统计所有文档中每个 token 的出现频率
    #   3. 排除已经在 query 中出现的 token
    #   4. 取频率最高的 top_n_terms 个 token
    #   5. 拼接到 query 后面，返回扩展后的查询
    def tokenize(text: str) -> set[str]:
        chars = [c for c in text if c not in "，。！？；：、\"'（）\n "]
        bigrams = {chars[i] + chars[i + 1] for i in range(len(chars) - 1)}
        return bigrams | set(chars)

    all_tokens: set[str] = set()
    for init_input in initial_results:
        tokens = tokenize(init_input)
        all_tokens.update(tokens)
    result = []
    for token in all_tokens:
        count = sum(1 for item in initial_results if token in item)
        result.append((token, count))

    result = [(t, c) for t, c in result if t not in query]
    result.sort(key=lambda x: x[1], reverse=True)

    new_terms = [t for t, _ in result[:top_n_terms]]
    return query + " " + " ".join(new_terms)


def task4():
    """
    目标：实现查询扩展，观察扩展后检索效果的改善。

    场景：用户的查询很短（如"怎么退"），但知识库中有"退货政策"、"退款时效"
          等更精确的术语。查询扩展可以桥接这个"词汇鸿沟"。

    运行：uv run python code/04-rag/retrieval-strategies/step3_tasks.py 4
    """
    model = get_model()
    doc_embeddings = [model.encode(doc) for doc in DOCUMENTS]

    # 使用刻意简化的短查询（模拟用户只输入关键词的场景）
    short_queries = [
        ("怎么退", "退货政策、退款时效"),
        ("运费", "国际配送、国内配送"),
        ("会员", "会员积分、会员等级"),
    ]

    print("=" * 65)
    print("任务 ④：查询扩展（Query Expansion）")
    print("=" * 65)

    for short_query, expected_docs in short_queries:
        print(f"\n{'─' * 50}")
        print(f'📝 原始查询: "{short_query}"（期望命中: {expected_docs}）')

        # 先用短查询做一次检索（Top-3）
        query_emb = model.encode(short_query)
        semantic_scores = [
            cosine_similarity(query_emb, doc_embeddings[i])
            for i in range(len(DOCUMENTS))
        ]
        top_k_indices = np.argsort(semantic_scores)[::-1][:3]

        print(f"   原始检索 Top-3:")
        for rank, idx in enumerate(top_k_indices):
            print(
                f"     #{rank+1} [{idx}] {DOCUMENTS[idx].split('：')[0]} (相似度={semantic_scores[idx]:.3f})"
            )

        # 用 Top-3 文档扩展查询
        retrieved_docs = [DOCUMENTS[idx] for idx in top_k_indices]
        expanded_query = expand_query(short_query, retrieved_docs)

        if expanded_query:
            print(f'\n   扩展后查询: "{expanded_query}"')

            # 用扩展后的查询再检索一次
            expanded_emb = model.encode(expanded_query)
            expanded_scores = [
                cosine_similarity(expanded_emb, doc_embeddings[i])
                for i in range(len(DOCUMENTS))
            ]
            expanded_indices = np.argsort(expanded_scores)[::-1][:3]

            print(f"   扩展后检索 Top-3:")
            for rank, idx in enumerate(expanded_indices):
                print(
                    f"     #{rank+1} [{idx}] {DOCUMENTS[idx].split('：')[0]} (相似度={expanded_scores[idx]:.3f})"
                )
        else:
            print(f"\n   ⚠️  expand_query() 尚未实现，请完成后再运行。")


# ═══════════════════════════════════════════════════════════════
# 主入口：命令行参数分发
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请指定任务编号：")
        print("  uv run python code/04-rag/retrieval-strategies/step3_tasks.py 1")
        print("  uv run python code/04-rag/retrieval-strategies/step3_tasks.py 2")
        print("  uv run python code/04-rag/retrieval-strategies/step3_tasks.py 3")
        print("  uv run python code/04-rag/retrieval-strategies/step3_tasks.py 4")
        sys.exit(1)

    task_num = sys.argv[1]
    tasks = {
        "1": task1,
        "2": task2,
        "3": task3,
        "4": task4,
    }

    if task_num not in tasks:
        print(f"未知任务编号: {task_num}，请使用 1-4")
        sys.exit(1)

    tasks[task_num]()
