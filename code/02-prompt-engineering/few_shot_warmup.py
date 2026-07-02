"""
模块 2 — Step 0 热身：Few-shot vs Zero-shot Prompting
直观感受"给不给示例"对模型输出质量的巨大影响

运行方式：
    cd code/02-prompt-engineering
    python few_shot_warmup.py
"""

import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# ── 初始化（boilerplate，和你模块1用的完全一样）──────────────────────
load_dotenv()  # 自动向上查找项目根目录的 .env
http_client = httpx.Client(trust_env=False)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    http_client=http_client,
)

MODEL = "deepseek-v4-flash"


def call_llm(system_prompt: str, user_input: str) -> str:
    """封装一次 LLM 调用（减少重复代码）"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.3,  # 低温度让分类任务更稳定
    )
    return response.choices[0].message.content


# ══════════════════════════════════════════════════════════════════════
# 实验：情感分类任务 — 比较 Zero-shot 和 Few-shot 的表现
# ══════════════════════════════════════════════════════════════════════

print("=" * 60)
print("🔬 实验：Zero-shot vs Few-shot 情感分类")
print("=" * 60)

# ── 测试句子（包含一些需要"读懂潜台词"的例子）─────────────────────
test_sentences = [
    "这个手机用了一个月就卡了，真不错。",
    "等了两个小时才上菜，但是味道确实好。",
    "快递包装完好，物流也快，好评。",
    "客服态度真好，一个问题问了三遍才回答我。",
    "嗯，这个价格能买到这样的质量，我还能说什么呢。",
]

# ── 实验 A：Zero-shot（不给任何示例）──────────────────────────────
ZERO_SHOT_SYSTEM = """你是一个情感分析助手。请对用户输入的句子做情感分类。
只能输出以下三个标签之一：正面、负面、中性。
直接输出标签，不要解释。"""

print("\n📋 实验 A：Zero-shot（不给示例）")
print("-" * 40)

for sentence in test_sentences:
    result = call_llm(ZERO_SHOT_SYSTEM, sentence)
    print(f"  输入: {sentence}")
    print(f"  结果: {result}")
    print()

# ── 实验 B：Few-shot（给 3 个示例后，让模型理解"反讽也是负面"）───
FEW_SHOT_SYSTEM = """你是一个情感分析助手。请对用户输入的句子做情感分类。
只能输出以下三个标签之一：正面、负面、中性。

重要规则：
- "反讽"（表面夸实际贬）归为「负面」
- 如果句子同时包含正负两面，判断整体倾向

以下是示例：

示例1:
输入: "这家店服务太棒了，让我等了半个小时。"
输出: 负面

示例2:
输入: "物流很快，商品和描述一致，很满意。"
输出: 正面

示例3:
输入: "还行吧，不好不坏。"
输出: 中性

现在请分析用户输入。只输出标签。"""

print("\n📋 实验 B：Few-shot（3个示例 + 反讽规则）")
print("-" * 40)

for sentence in test_sentences:
    result = call_llm(FEW_SHOT_SYSTEM, sentence)
    print(f"  输入: {sentence}")
    print(f"  结果: {result}")
    print()


# ══════════════════════════════════════════════════════════════════════
# 对比总结
# ══════════════════════════════════════════════════════════════════════

print("=" * 60)
print("🧠 观察引导")
print("=" * 60)
print("""
看一下上面两组结果，特别注意这些句子：
  - "这个手机用了一个月就卡了，真不错。" → 反讽，应该是「负面」
  - "客服态度真好，一个问题问了三遍才回答我。" → 反讽，应该是「负面」
  - "嗯，这个价格能买到这样的质量，我还能说什么呢。" → 反讽，应该是「负面」

Zero-shot 和 Few-shot 的结果一样吗？
如果不一致——为什么加了 3 个示例就能改变结果？
""")
