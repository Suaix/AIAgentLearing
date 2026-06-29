"""
Tokenization 实验 — Step 0 热身运行
====================================
目标：通过动手实验理解"模型看到的不是文字，而是 Token"这个核心概念。

运行方法：
    python code/01-foundations/tokenization_lab.py

依赖：tiktoken (OpenAI 开源的 BPE tokenizer)
"""

import tiktoken
import hashlib

SEPARATOR = "=" * 65
SUBSEP = "-" * 50


# ============================================================
# 实验 1：什么是 Token？—— 不同语言的"翻译"
# ============================================================
def experiment_1_basic():
    """展示中英文 / 代码 / 特殊字符对应的 token 数量和形态"""
    print(f"\n{SEPARATOR}")
    print("🔬 实验 1：同一句话，不同语言 → 不同的 Token 数")
    print(SEPARATOR)

    enc = tiktoken.get_encoding("cl100k_base")  # GPT-4 / Claude 使用的类似编码

    texts = {
        "英文": "The quick brown fox jumps over the lazy dog.",
        "中文": "敏捷的棕色狐狸跳过了懒惰的狗。",
        "代码": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
        "Emoji": "I ❤️ AI 🤖 and LLM 📚",
        "空格缩进": "    " * 5 + "indented_code()",
    }

    for label, text in texts.items():
        tokens = enc.encode(text)
        token_strs = [enc.decode([t]) for t in tokens]

        print(f"\n📝 {label} (共 {len(tokens)} tokens):")
        print(f"   原文: {text[:60]}{'...' if len(text) > 60 else ''}")
        print(f"   Token 序列: {token_strs}")
        print(f"   Token IDs: {tokens}")

    # 关键对比
    eng_tokens = len(enc.encode(texts["英文"]))
    chn_tokens = len(enc.encode(texts["中文"]))
    print(f"\n💡 关键发现：同样语义，中文用 {chn_tokens} tokens，英文用 {eng_tokens} tokens")
    print(f"   中文 token 效率约为英文的 {eng_tokens / chn_tokens:.0%}")


# ============================================================
# 实验 2：BPE 是怎么把文字切成 token 的？
# ============================================================
def experiment_2_bpe_merge():
    """模拟 BPE 合并过程——理解为什么某些词被拆成多个 token"""
    print(f"\n{SEPARATOR}")
    print("🔬 实验 2：BPE 合并过程——为什么同一个词有时完整、有时被拆分？")
    print(SEPARATOR)

    enc = tiktoken.get_encoding("cl100k_base")

    test_words = [
        "learning",
        "unlearning",       # un + learning
        "tokenization",     # 罕见词，可能被拆分
        "unprecedented",
        "ChatGPT",
        "programming",
        "aaaaaaaaaaaaaah",  # 拼写变体
        "你好世界",
    ]

    for word in test_words:
        tokens = enc.encode(word)
        pieces = [enc.decode([t]) for t in tokens]
        if len(tokens) == 1:
            print(f"  ✅ \"{word}\" → 1 token (完整匹配)")
        else:
            print(f"  ✂️  \"{word}\" → {len(tokens)} tokens: {pieces}")


# ============================================================
# 实验 3：Token ID 与 词汇表大小
# ============================================================
def experiment_3_vocab():
    """了解词汇表大小、特殊 token"""
    print(f"\n{SEPARATOR}")
    print("🔬 实验 3：词汇表与 Special Tokens")
    print(SEPARATOR)

    enc = tiktoken.get_encoding("cl100k_base")

    print(f"   编码名称: {enc.name}")
    print(f"   词汇表大小: {enc.n_vocab:,} tokens")

    # 展示一些特殊 token
    # tiktoken 的 cl100k_base 特殊 token 从末尾开始
    print(f"\n   📌 特殊 Tokens:")
    special_tokens = {
        "End of Text": enc.eot_token,
        "填充 (PAD)": "无 (GPT 系列不使用 PAD token)",
    }
    for name, val in special_tokens.items():
        print(f"      {name}: {val}")

    # Token ID 的范围
    print(f"\n   Token ID 范围: 0 ~ {enc.n_vocab - 1}")
    print(f"   每个 token 在词汇表中对应一个唯一的整数 ID")


# ============================================================
# 实验 4：Token 计数 → 成本估算
# ============================================================
def experiment_4_cost():
    """从 token 数推算 API 调用成本"""
    print(f"\n{SEPARATOR}")
    print("🔬 实验 4：Token → 成本估算")
    print(SEPARATOR)

    enc = tiktoken.get_encoding("cl100k_base")

    # 模拟一段对话
    system_prompt = "You are a helpful AI assistant that explains complex topics in simple terms."
    user_messages = [
        "解释一下什么是 Transformer 模型？",
        "用小学生也能听懂的方式解释。",
        "能给我画一个 ASCII 示意图吗？",
    ]

    total_input_tokens = len(enc.encode(system_prompt))
    print(f"   System prompt: {len(enc.encode(system_prompt))} tokens → \"{system_prompt}\"")

    for i, msg in enumerate(user_messages):
        tokens = len(enc.encode(msg))
        total_input_tokens += tokens
        print(f"   第 {i+1} 轮 user: {tokens} tokens → \"{msg}\"")

    # 假设每轮 assistant 回复约 200 tokens
    estimated_output = 200 * len(user_messages)

    print(f"\n   📊 输入 tokens 合计: {total_input_tokens}")
    print(f"   📊 输出 tokens 估计: {estimated_output}")
    print(f"   📊 总 tokens: {total_input_tokens + estimated_output}")

    # 价格估算 (以 DeepSeek V3 为例：输入 ¥1/百万token, 输出 ¥4/百万token)
    # 用近似价格
    cost_in = total_input_tokens * 1 / 1_000_000
    cost_out = estimated_output * 4 / 1_000_000
    print(f"\n   💰 估算成本 (参考 DeepSeek V3 定价):")
    print(f"      输入: ¥{cost_in:.4f}")
    print(f"      输出: ¥{cost_out:.4f}")
    print(f"      合计: ¥{(cost_in + cost_out):.4f} (约 ¥{(cost_in + cost_out) * 100:.2f} 分)")
    print(f"\n   ⚠️  这只是 3 轮简单对话的成本。Token 管理直接影响钱包！")


# ============================================================
# 实验 5：相同语义，不同表述 → Token 数差异
# ============================================================
def experiment_5_phrasing():
    """展示用词选择如何影响 token 消耗"""
    print(f"\n{SEPARATOR}")
    print("🔬 实验 5：Prompt 措辞如何影响 Token 成本？")
    print(SEPARATOR)

    enc = tiktoken.get_encoding("cl100k_base")

    variants = [
        ("简洁版", "解释 Transformer。" * 3),
        ("详细版", "请详细解释一下 Transformer 模型的内部工作原理，包括自注意力机制和多头注意力的数学原理。" * 3),
        ("英文简洁", "Explain Transformer." * 3),
        ("英文详细", "Please provide a detailed explanation of the Transformer model's internal working principles, including self-attention mechanisms and multi-head attention mathematics." * 3),
    ]

    print(f"\n   {'版本':<12} {'Tokens':<8} {'相对成本':<10} 内容预览")
    print(f"   {SUBSEP}")

    base_cost = None
    for label, text in variants:
        tokens = len(enc.encode(text))
        if base_cost is None:
            base_cost = tokens
        ratio = tokens / base_cost
        bar = "█" * int(ratio * 20) if ratio <= 3 else "█" * 60 + f"...({ratio:.0f}x)"
        print(f"   {label:<12} {tokens:<8} {ratio:.1f}x{'':<6} {bar}")

    print(f"\n   💡 同样在说 '解释 Transformer'，措辞选择让 token 消耗差出几倍")
    print(f"   这就是 Prompt Engineering 中'简洁即省钱'的硬道理")


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    print("🧬 Tokenization 实验平台")
    print("理解 LLM 最基本的问题：模型如何 '看到' 文字？\n")

    experiment_1_basic()
    experiment_2_bpe_merge()
    experiment_3_vocab()
    experiment_4_cost()
    experiment_5_phrasing()

    print(f"\n{SEPARATOR}")
    print("✅ 5 个实验全部完成！")
    print("接下来进入 Step 1 — 看看你观察到了什么 👇")
    print(SEPARATOR)
