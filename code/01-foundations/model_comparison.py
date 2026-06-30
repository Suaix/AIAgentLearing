"""
Step 0 热身：主流模型对比
======================
一次 Prompt，同时调用多个模型，对比回复风格、速度和成本。
"""

import time
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ═══════════════════════════════════════════════════════════
# 模型对比矩阵
# ═══════════════════════════════════════════════════════════

# 每个模型的配置：id、厂商、大致价格（每百万 token）
MODELS = [
    {
        "id": "deepseek-chat",              # DeepSeek V3
        "provider": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "price_input": 0.27,   # $/1M tokens
        "price_output": 1.10,  # $/1M tokens
        "note": "性价比之王，中文强",
    },
    {
        "id": "claude-fable-5",             # 需要 Anthropic API Key
        "provider": "Anthropic",
        "api_base": None,       # 留空 = 不调用（仅展示对比信息）
        "price_input": 3.00,
        "price_output": 15.00,
        "note": "复杂推理、长上下文、代码生成强",
    },
    {
        "id": "gpt-4o",                     # 需要 OpenAI API Key
        "provider": "OpenAI",
        "api_base": None,
        "price_input": 2.50,
        "price_output": 10.00,
        "note": "多模态、通用能力强、生态最完善",
    },
    {
        "id": "gemini-2.5-pro",             # 需要 Google API Key
        "provider": "Google",
        "api_base": None,
        "price_input": 1.25,
        "price_output": 10.00,
        "note": "超长上下文(1M+)、多模态、免费层慷慨",
    },
    {
        "id": "llama-4-maverick",           # 开源模型（需自部署或 API）
        "provider": "Meta (开源)",
        "api_base": None,
        "price_input": 0.20,
        "price_output": 0.60,
        "note": "开源可自部署、数据隐私、可微调",
    },
]

# ═══════════════════════════════════════════════════════════
# 测试 Prompt（设计成能暴露模型差异的任务）
# ═══════════════════════════════════════════════════════════

TEST_PROMPTS = [
    {
        "name": "创意写作",
        "prompt": "用一句话描述「下雨天」，要有画面感。",
        "what_to_watch": "语言风格、意象选择、句子长度",
    },
    {
        "name": "逻辑推理",
        "prompt": (
            "小明比小红大，小红比小刚大，小刚比小明小。"
            "请问：这三个人中谁最大？谁最小？请分析你的推理过程。"
        ),
        "what_to_watch": "推理步骤是否清晰、是否发现信息冗余",
    },
    {
        "name": "代码生成",
        "prompt": "用 Python 写一个函数，判断一个字符串是否是回文。要求一行代码。",
        "what_to_watch": "代码简洁性、是否考虑边界条件",
    },
]

# ═══════════════════════════════════════════════════════════
# 核心：对比函数
# ═══════════════════════════════════════════════════════════

def call_model(model_config, prompt, max_tokens=200):
    """调用单个模型，返回 (回复, 耗时, token用量, 成本)"""
    if model_config["api_base"] is None:
        return None, 0, None, 0  # 无 API Key，跳过

    client = OpenAI(
        api_key=os.getenv(f"{model_config['provider'].upper()}_API_KEY"),
        base_url=model_config["api_base"],
    )

    start = time.time()
    response = client.chat.completions.create(
        model=model_config["id"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    elapsed = time.time() - start

    usage = response.usage
    cost = (
        usage.prompt_tokens * model_config["price_input"]
        + usage.completion_tokens * model_config["price_output"]
    ) / 1_000_000

    return (
        response.choices[0].message.content,
        elapsed,
        usage,
        cost,
    )


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

print("=" * 70)
print("🧪 主流模型横向对比")
print("=" * 70)

# 1. 价格对比表
print("\n📊 一、模型概览（价格 / 1M tokens）\n")
print(f"{'模型':<22} {'厂商':<15} {'输入$':>8} {'输出$':>8} {'定位'}")
print("-" * 70)
for m in MODELS:
    print(f"  {m['id']:<20} {m['provider']:<15} "
          f"${m['price_input']:>6.2f}  ${m['price_output']:>7.2f}  "
          f"{m['note']}")

# 2. 逐任务对比
available = [m for m in MODELS if m["api_base"] is not None]

if not available:
    print("\n⚠️  未配置任何模型的 API Key，仅展示对比框架。")
    print("   请设置 DEEPSEEK_API_KEY 环境变量后重新运行。")
    exit(0)

for task in TEST_PROMPTS:
    print(f"\n{'='*70}")
    print(f"📝 任务：{task['name']}")
    print(f"   Prompt: {task['prompt']}")
    print(f"   👀 观察点: {task['what_to_watch']}")

    results = {}
    for m in available:
        provider = m["provider"]
        print(f"\n  --- {m['id']} ({provider}) ---")
        reply, elapsed, usage, cost = call_model(m, task["prompt"])

        if reply is None:
            print(f"  ⚠️  未配置 API Key，跳过")
            continue

        results[provider] = {
            "reply": reply,
            "elapsed": elapsed,
            "tokens_in": usage.prompt_tokens,
            "tokens_out": usage.completion_tokens,
            "cost": cost,
        }

        # 截断显示（长的回复只显示前 200 字符）
        display = reply[:200] + "..." if len(reply) > 200 else reply
        print(f"  回复: {display}")
        print(f"  ⏱️  {elapsed:.2f}s  |  "
              f"Tokens: {usage.prompt_tokens}→{usage.completion_tokens}  |  "
              f"💰 ${cost:.6f}")

    # 横向对比总结
    if len(results) >= 2:
        print(f"\n  📊 横向对比：")
        providers_list = list(results.keys())
        for key in ["elapsed", "cost"]:
            vals = [(p, results[p][key]) for p in providers_list]
            vals.sort(key=lambda x: x[1])
            label = "速度" if key == "elapsed" else "成本"
            ranking = " > ".join(f"{p}({v:.2f})" for p, v in vals)
            print(f"     {label}: {ranking}")

print(f"\n{'='*70}")
print("✅ 对比完成。观察要点：")
print("   1. 同一 Prompt，不同模型回复风格有何差异？")
print("   2. 速度和成本差异有多大？")
print("   3. 哪个模型在哪类任务上表现最好？")
print("=" * 70)
