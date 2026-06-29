"""
Tokenization Step 3 — 引导式修改练习
======================================
4 个渐进任务：改参数 → 加功能 → 修 bug → 扩展场景

运行方法：
    python code/01-foundations/tokenization_step3.py
"""

import sys
import tiktoken
from typing import List, Tuple

SEP = "=" * 60

# ──────────────────────────────────────────────
# 任务 ①：换一个 Tokenizer 编码
# ──────────────────────────────────────────────

def task1_compare_encodings():
    """
    目标：同一段文本，用不同编码器 tokenize，对比差异

    TODO ①：在下面 4 个编码器中选 2 个你没用过的，填入列表
    可用的编码器：
        - "cl100k_base"  (GPT-4 / GPT-3.5-turbo)
        - "o200k_base"   (GPT-4o / GPT-4o-mini)
        - "p50k_base"    (GPT-3 Codex / text-davinci)
        - "r50k_base"    (GPT-3 Davinci)
    """
    print(f"\n{SEP}")
    print("📝 任务 ①：对比不同 Tokenizer 编码结果")
    print(SEP)

    # text = "The Transformer architecture revolutionized natural language processing."
    text = "人工智能正在改变世界"

    encodings_to_try = ["cl100k_base", "o200k_base", "p50k_base"]  # ← TODO ①：再加 1-2 个编码器

    results = {}
    for enc_name in encodings_to_try:
        try:
            enc = tiktoken.get_encoding(enc_name)
            tokens = enc.encode(text)
            results[enc_name] = len(tokens)
        except Exception as e:
            print(f"   ❌ {enc_name}: {e}")

    print(f"\n   文本: \"{text}\"")
    print(f"   {'编码器':<20} {'Token 数':<10}")
    print(f"   {'-'*30}")
    for name, count in results.items():
        marker = " ← cl100k_base (基准)" if name == "cl100k_base" else ""
        print(f"   {name:<20} {count:<10}{marker}")

    if len(results) > 1:
        # 找差异
        counts = list(results.values())
        if counts[0] != counts[-1]:
            print(f"\n   💡 发现：不同编码器对同一文本的 token 数不同！")
            print(f"   原因：不同模型的词汇表内容不同（大小、训练语料都不同）")

    # ─── 预测题 ───
    print(f"\n   🎯 预测：下面这段中文用 'o200k_base' 编码，token 数会比 cl100k_base 多还是少？为什么？")
    chinese = "人工智能正在改变世界"
    cl100k = tiktoken.get_encoding("cl100k_base")
    print(f"      cl100k_base: {len(cl100k.encode(chinese))} tokens")
    print(f"      → 你的预测（多/少/差不多）：______")
    print(f"      理由：______")


# ──────────────────────────────────────────────
# 任务 ②：实现"Token 预算管理器"
# ──────────────────────────────────────────────

def count_messages_tokens(messages: List[dict], enc_name: str = "cl100k_base") -> int:
    """
    TODO ②：实现这个函数，计算一个 messages 列表的总 token 数

    提示：每条消息除了内容 text 本身，OpenAI API 还会给每条消息加
    ~3-4 tokens 的格式开销（role + 分隔符）。

    messages 格式示例：
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]
    """
    enc = tiktoken.get_encoding(enc_name)

    # TODO ②：填下面的代码
    # 你需要：
    #   1. 初始化 total = 0
    #   2. 遍历每条消息，编码 content，加到 total
    #   3. 每条消息加 4 tokens 的格式开销
    #   4. 最后加 2 tokens（对话结束标记）
    #   5. 返回 total

    total = 0

    # ─── 在这里写你的代码 ───

    for msg in messages:
        content_tokens = len(enc.encode(msg["content"]))
        total += content_tokens + 4  # 每条消息加 4 tokens 的格式开销

    total += 2  # 对话结束标记

    # ─────────────────────────

    return total


def task2_token_budget():
    """
    目标：实现一个工具函数，计算对话还剩多少 token 空间

    场景：你的模型 Context Window = 4096 tokens，
    你需要知道在发下一轮请求前，还能放多少内容。
    """
    print(f"\n{SEP}")
    print("📝 任务 ②：Token 预算管理器")
    print(SEP)

    # 测试数据
    test_messages = [
        {"role": "system", "content": "你是中英文双语翻译助手，把用户输入翻译成英文。"},
        {"role": "user", "content": "今天天气真好，我想去公园散步。"},
        {"role": "assistant", "content": "The weather is really nice today, I want to go for a walk in the park."},
        {"role": "user", "content": "那如果下雨呢？"},
    ]

    total = count_messages_tokens(test_messages)
    max_context = 4096
    remaining = max_context - total

    print(f"   当前对话: {total} tokens")
    print(f"   Context Window 上限: {max_context} tokens")
    print(f"   剩余空间: {remaining} tokens ({remaining / max_context:.1%})")

    if remaining > 0:
        print(f"   ✅ 还能放约 {remaining // 4} 个中文字 (按每字 4 tokens 估算)")
    else:
        print(f"   ⚠️ 超出上限！需要裁剪历史消息")

    print(f"\n   💡 预期输出参考：cl100k_base 下这 4 条消息约 60-80 tokens")


# ──────────────────────────────────────────────
# 任务 ③：修 Bug — Token 截断函数
# ──────────────────────────────────────────────

def truncate_by_tokens(text: str, max_tokens: int, enc_name: str = "cl100k_base") -> str:
    """
    按 token 数截断文本（保持可解码）

    ⚠️ 这个函数有 bug！运行 task3 看实际行为，然后修复它。

    期望行为：
        len(encode(truncate_by_tokens(text, N))) <= N

    实际行为：
        在某些情况下 token 数会超过 max_tokens（中文尤其明显）
    """
    enc = tiktoken.get_encoding(enc_name)
    tokens = enc.encode(text)

    # BUG 在这里：
    # 当前逻辑：裁剪 token 列表，然后用 enc.decode 解码回去
    # 问题：decode 可能把某些边界 token 合并，导致重新编码后 token 数变化
    # 修复方法：用 enc.decode 后再 enc.encode 检查，如果不满足就减一个 token 再试

    truncated_tokens = tokens[:max_tokens]
    result = enc.decode(truncated_tokens)

    # ─── TODO ③：在这下面加验证循环 ───
    # while... 循环检查 len(encode(result)) > max_tokens
    # 如果超出，就少取一个 token 再 decode
    # （提示：用 tokens[:max_tokens - n] 逐步回退）

    step = 1
    while len(enc.encode(result)) > max_tokens:
        truncated_tokens = tokens[:max_tokens - step]
        result = enc.decode(truncated_tokens)
        step += 1

    # ─────────────────────────────

    return result


def task3_fix_bug():
    """
    目标：发现并修复 token 截断函数的 bug
    """
    print(f"\n{SEP}")
    print("📝 任务 ③：修复 Token 截断 Bug")
    print(SEP)

    test_cases = [
        ("英文短文本", "Hello world, this is a test of truncation.", 5),
        ("中文短文本", "今天天气真好，我想去公园散步", 8),
        ("中英混合", "Transformer 模型的注意力机制非常强大。", 10),
    ]

    for label, text, max_tok in test_cases:
        result = truncate_by_tokens(text, max_tok)
        actual_tokens = len(tiktoken.get_encoding("cl100k_base").encode(result))

        status = "✅" if actual_tokens <= max_tok else "❌ BUG"
        print(f"\n   [{status}] {label} (限制 {max_tok} tokens)")
        print(f"      截断结果: \"{result}\"")
        print(f"      实际 tokens: {actual_tokens} / {max_tok}")

        if actual_tokens > max_tok:
            print(f"      ⚠️ 超出 {actual_tokens - max_tok} 个 token！这就是 bug")

    print(f"\n   💡 提示：decode 不保证重新编码后 token 数不变")
    print(f"   尤其是中文，被拆成字节级 token 后又拼接回去，token 边界会漂移")


# ──────────────────────────────────────────────
# 任务 ④：扩展到新场景 — 估算实际 API 调用成本
# ──────────────────────────────────────────────

def estimate_api_cost(
    system_prompt: str,
    user_input: str,
    model: str = "deepseek-chat",
    estimated_output_tokens: int = 200,
) -> dict:
    """
    TODO ④：整合今天学的内容，估算一次 API 调用的总成本

    需求：
    1. 用 tiktoken 计算 system_prompt + user_input 的 token 数
    2. 加上格式开销（约每条消息 4 tokens + 结尾 2 tokens）
    3. 根据模型定价计算成本

    DeepSeek 定价参考 (per 1M tokens):
        deepseek-chat (V3):    输入 ¥1.0,  输出 ¥4.0
        deepseek-reasoner (R1): 输入 ¥4.0,  输出 ¥16.0

    返回格式:
        {
            "input_tokens": int,
            "estimated_output_tokens": int,
            "total_tokens": int,
            "cost_rmb": float,
        }
    """
    enc = tiktoken.get_encoding("o200k_base")  # 假设 DeepSeek V3 用这个编码器

    # 模型定价表
    pricing = {
        "deepseek-chat":     {"input": 1.0,  "output": 4.0},
        "deepseek-reasoner": {"input": 4.0,  "output": 16.0},
        "gpt-4o":           {"input": 18.5, "output": 55.5},  # 参考价 USD 近似
    }

    # ─── TODO ④：填下面的代码 ───

    # 1. 编码 system_prompt 和 user_input
    # input_tokens = ...
    input_tokens = len(enc.encode(system_prompt)) + len(enc.encode(user_input))

    # 2. 加格式开销
    # total_input_tokens = input_tokens + ...
    total_input_tokens = input_tokens + 4 * 2 + 2  # 两条消息 + 结尾

    # 3. 查模型定价
    # price = pricing.get(model, ...)
    price = pricing.get(model, {"input": 1.0, "output": 4.0})  # 默认价格
    # 4. 计算成本
    # cost = ...
    cost = total_input_tokens * price["input"] / 1_000_000 + estimated_output_tokens * price["output"] / 1_000_000

    # ─────────────────────────────

    return {
        "input_tokens": total_input_tokens,            # TODO：替换为实际值
        "estimated_output_tokens": estimated_output_tokens,
        "total_tokens": total_input_tokens + estimated_output_tokens,            # TODO：替换为实际值
        "cost_rmb": cost,              # TODO：替换为实际值
    }


def task4_extend():
    """
    目标：把 token 知识用在真实场景——做一次 API 调用成本预估
    """
    print(f"\n{SEP}")
    print("📝 任务 ④：估算 API 调用成本")
    print(SEP)

    # 模拟场景：你要调用 API 做一个技术翻译
    system = "你是一个专业的技术文档中英翻译助手。保持术语一致性，保留代码块不翻译。"
    user = """
请把以下技术文档翻译成英文：

# API 接口文档
## 用户认证
使用 Bearer Token 进行身份验证，Token 通过 /auth/login 接口获取。
请求头需携带 `Authorization: Bearer <your_token>`。
"""

    models_to_check = ["deepseek-chat", "deepseek-reasoner", "gpt-4o"]

    print(f"   System Prompt: {len(system)} 字符")
    print(f"   User Input: {len(user)} 字符")
    print(f"   预估输出长度: 200 tokens\n")

    for model in models_to_check:
        result = estimate_api_cost(system, user, model=model)
        print(f"   🤖 {model}:")
        print(f"      Input: {result['input_tokens']} tokens")
        print(f"      Output (估): {result['estimated_output_tokens']} tokens")
        print(f"      Total: {result['total_tokens']} tokens")
        print(f"      Cost: ¥{result['cost_rmb']:.6f}")

    print(f"\n   💡 对比：同样一次调用，不同模型价格可以差几十倍")


# ============================================================
# 主入口：通过命令行参数指定要运行的任务
# 用法：
#   python tokenization_step3.py 1         → 只运行任务①
#   python tokenization_step3.py 1 2 3     → 运行任务①②③
#   python tokenization_step3.py            → 运行全部
# ============================================================
if __name__ == "__main__":
    # 解析参数
    if len(sys.argv) > 1:
        task_nums = {int(a) for a in sys.argv[1:]}
    else:
        task_nums = {1, 2, 3, 4}  # 默认全部

    TASKS = {
        1: ("对比 Tokenizer 编码", task1_compare_encodings),
        2: ("Token 预算管理器", task2_token_budget),
        3: ("修复 Token 截断 Bug", task3_fix_bug),
        4: ("估算 API 调用成本", task4_extend),
    }

    selected = sorted(task_nums)
    print(f"🧪 Tokenization Step 3 — 运行任务: {selected}\n")

    for num in selected:
        if num in TASKS:
            print(f"▶️  任务 {num}：{TASKS[num][0]}")
            TASKS[num][1]()
        else:
            print(f"⚠️  任务 {num} 不存在，请使用 1-4")

    print(f"\n{SEP}")
    print(f"✅ 选定任务 {selected} 运行完成")
    print(f"   用法: python tokenization_step3.py [任务号...]  如 'python tokenization_step3.py 1'")
    print(SEP)
