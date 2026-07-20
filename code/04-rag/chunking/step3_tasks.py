"""
Step 3 — 文档分块策略：引导式修改任务

四个任务通过命令行参数选择：
  uv run python code/04-rag/chunking/step3_tasks.py 1   # 改参数：实验不同chunk_size
  uv run python code/04-rag/chunking/step3_tasks.py 2   # 加功能：实现语义分块
  uv run python code/04-rag/chunking/step3_tasks.py 3   # 修Bug：阈值条件反了
  uv run python code/04-rag/chunking/step3_tasks.py 4   # 扩展：构建可配置检索器
"""

from regex import F
from sentence_transformers import SentenceTransformer
import numpy as np
import sys

from torch import chunk, embedding, threshold

# ═══════════════════════════════════════════════════════
# 共享工具函数（已实现，无需修改）
# ═══════════════════════════════════════════════════════


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def load_article() -> tuple[list[str], str]:
    """加载 Step 0 中的多主题文章，返回（句子列表, 原文）"""
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

    sentences = [
        s.strip() for s in full_article.replace("\n", "").split("。") if s.strip()
    ]
    return sentences, full_article


def fixed_chunk(sentences: list[str], chunk_size: int) -> list[str]:
    """固定大小分块：每 chunk_size 句一块"""
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = "。".join(sentences[i : i + chunk_size]) + "。"
        chunks.append(chunk)
    return chunks


def sliding_chunk(sentences: list[str], chunk_size: int, overlap: int = 1) -> list[str]:
    """滑动窗口分块：每 chunk_size 句一块，相邻窗口重叠 overlap 句"""
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(sentences) - overlap, step):
        chunk = "。".join(sentences[i : i + chunk_size]) + "。"
        chunks.append(chunk)
    return chunks


def retrieve(
    query: str, chunks: list[str], model: SentenceTransformer
) -> list[tuple[int, float, str]]:
    """检索：返回 [(chunk_index, similarity, chunk_text), ...] 按相似度降序"""
    query_emb = model.encode([query])[0]
    chunk_embs = model.encode(chunks)
    results = [
        (i, cosine_similarity(query_emb, chunk_embs[i]), chunks[i])
        for i in range(len(chunks))
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ═══════════════════════════════════════════════════════
# 任务 ①：改参数 — 实验不同 chunk_size 对检索的影响
# ═══════════════════════════════════════════════════════


def task1():
    """
    目标：对比 chunk_size=1, 2, 3, 5 时，同一查询的检索结果差异
    关键概念：精度（小块） vs 上下文完整性（大块）的 tradeoff

    预测后再运行：
      - 对"什么是RAG？"，哪个 chunk_size 相似度最高？
      - chunk_size=5 时，"机器学习有哪些常见算法？"的Top-1块还纯粹吗？

    运行：uv run python code/04-rag/chunking/step3_tasks.py 1
    """
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    sentences, _ = load_article()

    queries = [
        "什么是 RAG？",
        "深度学习框架有哪些？",
        "机器学习有哪些常见算法？",
    ]

    chunk_sizes = [1, 2, 3, 5]

    print("=" * 60)
    print("任务 ①：不同 chunk_size 对检索的影响")
    print("=" * 60)
    print(f"文章共 {len(sentences)} 句话\n")

    # TODO: 对每个 chunk_size，展示检索结果
    # 提示：
    #   1. 用 fixed_chunk(sentences, size) 分块
    #   2. 打印 "  [chunk_size={size}, 共{len(chunks)}块]"
    #   3. 对每个查询调用 retrieve(query, chunks, model)
    #   4. 打印 Top-1 的相似度和块内容（前100字即可）
    for size in chunk_sizes:
        chunks = fixed_chunk(sentences, size)
        print(f"  [chunk_size={size}, 共{len(chunks)}块]")
        for query in queries:
            print(f"查询内容：{query}")
            result = retrieve(query, chunks, model)
            print(f"Top-1 相似度：{result[0][1]}, 块内容：{result[0][2][:100]}")

    print("\n📝 回答问题：")
    print("Q1: 哪个 chunk_size 对'什么是RAG？'的相似度最高？为什么？")
    print("    你的答案：...")
    print(
        "Q2: chunk_size=5 时，'机器学习有哪些常见算法？'的Top-1块内容是什么？混入了什么无关内容？"
    )
    print("    你的答案：...")


# ═══════════════════════════════════════════════════════
# 任务 ②：加功能 — 实现语义分块 (Semantic Chunking)
# ═══════════════════════════════════════════════════════


def semantic_chunk(
    sentences: list[str], model: SentenceTransformer, threshold: float
) -> list[str]:
    """按语义相似度分块：相邻句子相似度 < threshold 时作为切分点"""
    if not sentences:
        return []

    embeddings = model.encode(sentences)
    current_chunk = [sentences[0]]
    chunks = []
    for i in range(1, len(sentences)):
        sim = cosine_similarity(embeddings[i - 1], embeddings[i])
        if sim < threshold:
            temp_sen = None
            for sen in current_chunk:
                if temp_sen:
                    temp_sen = temp_sen + sen + "。"
                else:
                    temp_sen = sen
            chunks.append(temp_sen)
            # 添加完成后清空current_chunk
            current_chunk.clear()
        current_chunk.append(sentences[i])

    if len(current_chunk) > 0:
        # 还有未添加的内容
        temp_sen = None
        for sen in current_chunk:
            if temp_sen:
                temp_sen = temp_sen + sen + "。"
            else:
                temp_sen = sen
        chunks.append(temp_sen)
    return chunks


def task2():
    """
    目标：实现 semantic_chunk() 函数
    算法：相邻句子语义相似度 < threshold → 切分点（主题转换）

    API 提示：
      model.encode(sentences)  →  np.ndarray, shape=(N, 384)
      cosine_similarity(emb[i-1], emb[i])  →  float

    运行：uv run python code/04-rag/chunking/step3_tasks.py 2
    """
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    sentences, _ = load_article()

    # 测试不同阈值
    print("=" * 60)
    print("任务 ②：语义分块 — 不同阈值的分块效果")
    print("=" * 60)

    for threshold in [0.3, 0.5, 0.7]:
        chunks = semantic_chunk(sentences, model, threshold)
        print(f"\n[threshold={threshold}] 共 {len(chunks)} 块：")
        for i, chunk in enumerate(chunks):
            print(f"  块[{i}] ({len(chunk)}字): {chunk[:100]}...")

    # 检索对比：固定分块 vs 语义分块
    query = "什么是 RAG？"
    print(f"\n{'─' * 60}")
    print(f'🔍 检索对比: "{query}"')

    fixed_chunks = fixed_chunk(sentences, 2)
    semantic_chunks = semantic_chunk(sentences, model, threshold=0.5)

    # TODO: 分别用两种策略检索，展示 Top-1 的结果
    # 提示：调用 retrieve(query, chunks, model) 然后取 [0]
    result1 = retrieve(query, fixed_chunks, model)
    result2 = retrieve(query, semantic_chunks, model)
    print(f"使用固定分块 Top-1 的结果：相似度={result1[0][1]}，块内容={result1[0][2]}")
    print(f"使用语义分块 Top-1 的结果：相似度={result2[0][1]}，块内容={result2[0][2]}")
    print("\n📝 回答问题：")
    print("Q: 语义分块在哪个阈值下最接近'每个块对应一个主题'？观察输出给出你的判断。")


# ═══════════════════════════════════════════════════════
# 任务 ③：修 Bug — 语义分块阈值条件反了
# ═══════════════════════════════════════════════════════


def task3():
    """
    目标：下面的 semantic_chunk_buggy() 包含一个 bug，导致分块结果完全异常。
          找到并修复它。

    调试思路：
      观察输出——相似度"高"的相邻句子被切开了，相似度"低"的反而合并在一起。
      这正好和语义分块的逻辑相反。找到那个方向反了的条件判断。

    运行：uv run python code/04-rag/chunking/step3_tasks.py 3
    """
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    sentences, _ = load_article()

    def semantic_chunk_buggy(
        sentences: list[str], model: SentenceTransformer, threshold: float
    ) -> list[str]:
        """语义分块 — 有 bug 的版本"""
        if not sentences:
            return []

        embeddings = model.encode(sentences)
        chunks = []
        current_chunk = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = cosine_similarity(embeddings[i - 1], embeddings[i])
            # ═══════════════════════════════════════════════
            if sim < threshold:  # ← 条件在这里
                chunks.append("。".join(current_chunk) + "。")
                current_chunk = [sentences[i]]
            else:
                current_chunk.append(sentences[i])
            # ═══════════════════════════════════════════════

        if current_chunk:
            chunks.append("。".join(current_chunk) + "。")

        return chunks

    # 诊断：打印相邻句子的相似度，帮助理解 bug
    print("=" * 60)
    print("任务 ③：修复语义分块的 Bug")
    print("=" * 60)

    embeddings = model.encode(sentences)
    print("\n📊 相邻句子相似度（用于诊断）：")
    for i in range(1, len(sentences)):
        sim = cosine_similarity(embeddings[i - 1], embeddings[i])
        marker = " ← 高相似（同主题）" if sim > 0.5 else " ← 低相似（主题转换）"
        print(f"  句{i-1}↔句{i}: sim={sim:.3f}{marker}")
        print(f"    句{i-1}: {sentences[i-1][:60]}...")
        print(f"    句{i}:  {sentences[i][:60]}...")

    print("\n❌ Bug 版本分块结果（threshold=0.5）：")
    buggy_chunks = semantic_chunk_buggy(sentences, model, threshold=0.5)
    for i, chunk in enumerate(buggy_chunks):
        print(f"  块[{i}]: {chunk[:120]}...")

    print("\n🔍 观察上面的输出，你发现了什么问题？")
    print("   提示：同主题的句子（如两句都讲机器学习）被切开了吗？")
    print("         不同主题的句子（如NLP→MLOps）反而合并了吗？")

    # TODO: 解释 bug 原因
    # TODO: 修复条件（把 >= 改成正确的关系），然后重新运行看看是否正确

    print("\n📝 回答问题：")
    print("Bug 原因：当 sim >= threshold（相似度'高'）时切分，这意味着...")
    print("    你的答案：刚命中这个主题就开始切分了，后续关联的概念都被切掉了")
    print("修复方式：把条件改成 sim < threshold")
    print(
        "    你的答案：将句子相似度开始小于阈值时进行切分，接下来的句子应该是跟该主题关联不大了"
    )


# ═══════════════════════════════════════════════════════
# 任务 ④：扩展 — 在新文档上构建可配置检索器
# ═══════════════════════════════════════════════════════


def task4():
    """
    目标：构建 build_retriever() 函数，接收文档+策略+查询，返回 Top-K 结果。
          用一篇关于 AI Agent 的新文档，对比三种分块策略的检索效果。

    运行：uv run python code/04-rag/chunking/step3_tasks.py 4
    """
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # 一篇关于 AI Agent 的新文档（来自你的学习路线图）
    new_document = """AI Agent 是一种能够自主感知环境、制定计划并执行行动的智能系统。
Agent 的核心组件包括感知模块、规划模块、执行模块和记忆模块四个部分。

Tool Use 是 Agent 的关键能力之一，它允许 Agent 调用外部工具和 API 来扩展自身能力。
Tool Definition 使用 JSON Schema 来精确定义每个工具的名称、参数和返回值类型。

RAG 技术通过检索外部知识库来增强 LLM 的生成质量，解决幻觉和知识截止问题。
文档分块是 RAG 系统的关键预处理步骤，分块大小直接影响检索精度和上下文完整性。

Prompt Engineering 是引导 LLM 行为的核心技术，包括 Few-shot、Chain-of-Thought 等方法。
System Prompt 定义了 Agent 的角色边界和安全约束，是 Agent 行为控制的基石。

多 Agent 协作系统通过多个专业 Agent 之间的通信和协调来完成复杂任务。
常见的多 Agent 模式包括顺序执行、并行处理、辩论机制和层级委派。"""

    sentences = [
        s.strip() for s in new_document.replace("\n", "").split("。") if s.strip()
    ]

    def build_retriever(
        sentences: list[str],
        strategy: str,  # "fixed" | "semantic" | "sliding"
        model: SentenceTransformer,
        query: str,
        top_k: int = 3,
        **kwargs,
    ) -> list[tuple[int, float, str]]:
        """
        可配置检索器

        kwargs 可包含：
          - chunk_size: int（fixed/sliding 策略用，默认 2）
          - overlap: int（sliding 策略用，默认 1）
          - threshold: float（semantic 策略用，默认 0.5）

        返回：[(chunk_index, similarity, chunk_text), ...] 按相似度降序，共 top_k 个
        """
        # TODO: 你的代码
        # 步骤：
        #   1. 从 kwargs 读取参数：chunk_size=kwargs.get("chunk_size", 2) 等
        #   2. 根据 strategy 选择分块方式：
        #      "fixed" → fixed_chunk(sentences, chunk_size)
        #      "sliding" → sliding_chunk(sentences, chunk_size, overlap)
        #      "semantic" → semantic_chunk(sentences, model, threshold)
        #      （semantic_chunk 直接用任务②里写好的）
        #   3. 调用 retrieve(query, chunks, model)
        #   4. 返回 top_k 个结果
        if top_k <= 0:
            return []

        chunks = []
        if strategy == "fixed":
            chunks = fixed_chunk(sentences, kwargs.get("chunk_size", 2))
        elif strategy == "sliding":
            chunks = sliding_chunk(
                sentences, kwargs.get("chunk_size", 2), overlap=kwargs.get("overlap", 1)
            )
        else:
            chunks = semantic_chunk(sentences, model, kwargs.get("threshold", 0.5))
        result = retrieve(query, chunks, model)
        if len(result) <= top_k:
            return result
        else:
            return result[:top_k]

    # 测试：一组查询，三种策略对比
    test_queries = [
        "Agent 有哪些核心组件？",
        "什么是 Tool Use？",
        "多 Agent 如何协作？",
        "Prompt Engineering 有哪些方法？",
    ]

    strategies = ["fixed", "semantic", "sliding"]

    print("=" * 60)
    print("任务 ④：可配置检索器 — 三种策略在新文档上的对比")
    print("=" * 60)
    print(
        f"新文档共 {len(sentences)} 句话，涵盖 Agent/工具/RAG/Prompt/多Agent 5个主题\n"
    )

    for query in test_queries:
        print(f'🔍 查询: "{query}"')
        # TODO: 对每种策略调用 build_retriever，展示 Top-1 相似度和块内容
        for strate in strategies:
            result = build_retriever(
                sentences, strate, model, query, top_k=3, chunk_size=2, threshold=0.5
            )
            print(f"{strate}策略\n")
            print(f"=" * 50)
            for i in range(len(result)):
                print(f"Top-{i+1}: 相似度={result[i][1]}, 块内容={result[i][2][:100]}")
            print(f"=" * 50)
        print()

    print("\n📝 回答问题：")
    print("Q: 三种策略在新文档上的表现有何差异？哪种最稳定？")
    print("    你的答案：固定分块策略最稳定")


# ═══════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请指定任务编号：")
        print("  uv run python code/04-rag/chunking/step3_tasks.py 1")
        print("  uv run python code/04-rag/chunking/step3_tasks.py 2")
        print("  uv run python code/04-rag/chunking/step3_tasks.py 3")
        print("  uv run python code/04-rag/chunking/step3_tasks.py 4")
        sys.exit(1)

    task_num = sys.argv[1]
    tasks = {"1": task1, "2": task2, "3": task3, "4": task4}

    if task_num not in tasks:
        print(f"未知任务编号: {task_num}，请输入 1-4")
        sys.exit(1)

    tasks[task_num]()
