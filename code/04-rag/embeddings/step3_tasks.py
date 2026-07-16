"""
Step 3 — Embedding 引导式修改
四个渐进任务，通过命令行参数选择：
  uv run python code/04-rag/embeddings/step3_tasks.py 1    # 任务①
  uv run python code/04-rag/embeddings/step3_tasks.py 2    # 任务②
  uv run python code/04-rag/embeddings/step3_tasks.py 3    # 任务③
  uv run python code/04-rag/embeddings/step3_tasks.py 4    # 任务④
"""

import sys
import numpy as np
from sentence_transformers import SentenceTransformer

# ══════════════════════════════════════════════════════════════
# 公共工具函数
# ══════════════════════════════════════════════════════════════


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def print_similarity_ranking(
    query: str, query_emb: np.ndarray, texts: list[str], embeddings: np.ndarray
):
    """打印相似度排名（按相似度降序）"""
    scores = [
        (i, cosine_similarity(query_emb, embeddings[i]), texts[i])
        for i in range(len(texts))
    ]
    scores.sort(key=lambda x: x[1], reverse=True)

    print(f'\n   查询: "{query}"')
    print(f"   {'─' * 50}")
    for rank, (idx, score, text) in enumerate(scores, 1):
        bar = "█" * max(1, int(score * 20))
        print(f"   #{rank} [{idx}] 相似度={score:.3f} {bar}")
        print(f'        "{text}"')


# ══════════════════════════════════════════════════════════════
# 任务① — 改参数：换模型对比效果
# ══════════════════════════════════════════════════════════════


def task1_change_model():
    """
    任务目标：对比两个模型的语义理解差异

    TODO ①-1：把下面这行里的模型名换成 "paraphrase-multilingual-MiniLM-L12-v2"
              （注意：这个模型更大，首次下载需要等待约 30 秒）
    """
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"  # TODO: 换成 multilingual 模型

    # 加载模型
    print(f"\n📦 当前模型: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"   向量维度: {model.get_sentence_embedding_dimension()}")

    # 相同的中英文句子对
    en_text = "Machine learning is transforming the world"
    zh_text = "机器学习正在改变世界"

    en_emb = model.encode([en_text])[0]
    zh_emb = model.encode([zh_text])[0]

    sim = cosine_similarity(en_emb, zh_emb)

    print(f'\n   英文: "{en_text}"')
    print(f'   中文: "{zh_text}"')
    print(f"   相似度: {sim:.3f}")

    # TODO ①-2：观察输出中的相似度数值，
    #           与 Step 0 中 all-MiniLM-L6-v2 的结果（0.094）对比，
    #           写一行注释说明你的发现。
    #
    # 你的发现：
    # TODO: (在这里写)
    print(f"相似度比之前模型的要大")
    # 预期输出（multilingual 模型）：
    #   相似度应该在 0.7 以上，因为该模型专门训练了跨语言语义对齐


# ══════════════════════════════════════════════════════════════
# 任务② — 加功能：构建微型文档检索引擎
# ══════════════════════════════════════════════════════════════


def task2_document_search():
    """
    任务目标：完成一个简单的文档检索引擎

    场景：有一个 FAQ 知识库，用户用自然语言提问，系统找到最相关的 FAQ 条目。
    """

    # 模拟 FAQ 知识库（10 条问答）
    faq_database = [
        "如何进行退款操作？请登录账户后前往订单页面点击申请退款。",
        "退货政策说明：自收到商品之日起7天内可申请无理由退货。",
        "如何修改收货地址？在个人设置中找到地址管理即可修改。",
        "配送时效：顺丰快递1-3个工作日，普通快递3-7个工作日。",
        "如何联系客服？在线客服工作时间为9:00-21:00，或拨打400-xxx-xxxx。",
        "账号被盗怎么办？请立即修改密码并联系客服冻结账号。",
        "优惠券使用方法：结算时在优惠券栏输入券码或选择已有优惠券。",
        "商品质量问题如何处理？请拍照并联系客服，核实后可换货或退款。",
        "如何查看订单物流？在订单详情页点击查看物流即可实时追踪。",
        "会员等级与权益：银卡9.5折、金卡9折、钻石卡8.5折，积分可抵现。",
    ]

    # 因为 FAQ 全是中文，需要切换到支持中文的模型
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print(f"\n📦 使用模型: paraphrase-multilingual-MiniLM-L12-v2")

    # 将所有 FAQ 预先编码为向量（生产环境中这一步只做一次，存到向量数据库）
    print("🔢 正在编码 FAQ 知识库...")
    # TODO ②-1：调用 model.encode() 将 faq_database 转换为向量
    #           存入变量 faq_embeddings
    faq_embeddings = model.encode(faq_database)

    # 用户查询
    user_queries = [
        "我要退货",
        "快递到哪了",
        "账号不安全了",
    ]

    for query in user_queries:
        # TODO ②-2：将 query 编码为向量，然后调用 print_similarity_ranking()
        #           找出最相关的 FAQ 条目
        query_emb = model.encode(query)
        print_similarity_ranking(query, query_emb, faq_database, faq_embeddings)

    # 预期输出示例（以 "我要退货" 为例）：
    #   #1 相似度最高 → "退货政策说明：自收到商品之日起7天内..."
    #   #2 次高      → "商品质量问题如何处理？请拍照并联系客服..."
    #   #3 更低      → 其他不相关的 FAQ


# ══════════════════════════════════════════════════════════════
# 任务③ — 修 Bug：向量归一化误区
# ══════════════════════════════════════════════════════════════


def euclidean_similarity_fixed(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    修复版：用线性映射代替 1/(1+d)。

    Bug 原因：model.encode() 已经输出归一化向量（||v||=1），
    所以 d ∈ [0, 2]。但 1/(1+d) 的取值范围是 [1/3, 1] = [0.333, 1.0]，
    永远无法给出低于 0.333 的分数——"不相关"也被迫拉高到 0.4+。
    改用 1 - d/2：d=0→1.0, d=2→0.0，范围完整展开。
    """
    distance = np.linalg.norm(vec1 - vec2)  # 向量已是单位向量，d ∈ [0, 2]
    similarity = 1.0 - distance / 2.0       # 线性映射到 [0, 1]
    return similarity


def task3_fix_bug():
    """
    任务目标：对比余弦相似度和欧氏距离相似度，找出不合理的结果并修复。
    """

    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 三组文本对
    pairs = [
        # (文本A, 文本B, 预期关系)
        ("I love pizza", "I really enjoy eating pizza", "高度相似"),
        ("I love pizza", "The weather is cold today", "不相关"),
        ("I love pizza", "Pizza is a popular Italian dish", "中度相似"),
    ]

    print("\n📊 对比两种相似度度量：")
    print(f"   {'─' * 60}")

    for text_a, text_b, expected in pairs:
        emb_a = model.encode([text_a])[0]
        emb_b = model.encode([text_b])[0]

        cos_sim = cosine_similarity(emb_a, emb_b)
        euc_sim = euclidean_similarity_fixed(emb_a, emb_b)

        # TODO ③-2：观察输出，哪个结果不符合预期？
        #           修复 euclidean_similarity_buggy 函数中的 bug。
        print(f'\n   A: "{text_a}"')
        print(f'   B: "{text_b}"')
        print(f"   预期: {expected}")
        print(f"   余弦相似度: {cos_sim:.3f}")
        print(f"   欧氏相似度: {euc_sim:.3f}")

    # TODO ③-3：修复 bug 后，写一行注释说明：
    #           为什么在这个场景下余弦比欧氏更合适？
    #
    # 你的回答：
    #


# ══════════════════════════════════════════════════════════════
# 任务④ — 扩展场景：混合语言 FAQ 检索
# ══════════════════════════════════════════════════════════════


def task4_multilingual_search():
    """
    任务目标：扩展任务②，支持用户用英文检索中文 FAQ

    场景：国际化电商平台，FAQ 是中文的，但可能有外国用户用英文提问。
    """

    faq_cn = [
        "退货政策：7天无理由退货，需保持商品完好。",
        "支付方式：支持微信支付、支付宝、银联卡。",
        "国际配送：DHL配送费按重量计算，时效5-10个工作日。",
        "发票开具：电子发票在订单完成后自动发送至注册邮箱。",
        "会员积分：每消费1元积1分，100分抵1元。",
    ]

    # 使用多语言模型
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # TODO ④-1：将 faq_cn 编码为向量
    faq_embeddings = model.encode(faq_cn)

    # 英文提问（用户不懂中文，用英文问）
    english_queries = [
        "How can I return a product?",  # 对应：退货政策
        "What payment methods do you accept?",  # 对应：支付方式
        "How do I earn reward points?",  # 对应：会员积分
    ]

    # TODO ④-2：对每个英文查询，编码后在中文 FAQ 中检索最相关的结果
    #           提示：和任务②完全相同的逻辑，只是查询语言变了！
    #           如果 multilingual 模型工作正常，英文查询应该能匹配到中文 FAQ。
    for query in english_queries:
        query_emb = model.encode(query)
        print_similarity_ranking(query, query_emb, faq_cn, faq_embeddings)

    # TODO ④-3：最后一个查询 "How do I earn reward points?" 应该匹配到哪条 FAQ？
    #           预测排名，然后运行验证。
    #
    # 你的预测：
    # # 1 会员积分：每消费1元积1分，100分抵1元。

    # 预期结果：英文查询能成功匹配到语义对应的中文 FAQ。
    # 这就是 cross-lingual retrieval，多语言 RAG 的基础。


# ══════════════════════════════════════════════════════════════
# 任务分发
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请指定任务编号：")
        print("  uv run python code/04-rag/embeddings/step3_tasks.py 1")
        print("  uv run python code/04-rag/embeddings/step3_tasks.py 2")
        print("  uv run python code/04-rag/embeddings/step3_tasks.py 3")
        print("  uv run python code/04-rag/embeddings/step3_tasks.py 4")
        sys.exit(1)

    task_num = sys.argv[1]
    tasks = {
        "1": ("改参数：换模型对比效果", task1_change_model),
        "2": ("加功能：构建微型文档检索引擎", task2_document_search),
        "3": ("修 Bug：向量归一化误区", task3_fix_bug),
        "4": ("扩展场景：混合语言 FAQ 检索", task4_multilingual_search),
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
