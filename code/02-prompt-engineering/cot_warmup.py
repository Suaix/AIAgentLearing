"""
模块 2 — Step 0 热身：Chain-of-Thought (CoT) Prompting
直观感受"让模型一步步想"对推理能力的巨大影响

运行方式：
    cd code/02-prompt-engineering
    python cot_warmup.py
"""

import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
http_client = httpx.Client(trust_env=False)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    http_client=http_client,
)
MODEL = "deepseek-v4-flash"


def call_llm(system_prompt: str, user_input: str, temperature: float = 0.0) -> str:
    """封装 LLM 调用"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content


# ══════════════════════════════════════════════════════════════════════
# 实验题目（选自需要多步推理的问题）
# ══════════════════════════════════════════════════════════════════════

problems = [
    {
        "id": "数学推理",
        "question": """小明有 15 个苹果，他给了小红 1/3，又给了小李剩下苹果的一半。
然后他吃了 2 个苹果。请问小明现在还有几个苹果？""",
        "answer": "3 个",
        "steps": """1. 小明一开始有 15 个苹果
2. 给小红 1/3：15 × 1/3 = 5 个，剩下 15 - 5 = 10 个
3. 给小李剩下的一半：10 ÷ 2 = 5 个，剩下 10 - 5 = 5 个
4. 吃掉 2 个：5 - 2 = 3 个
5. 答案：3 个""",
    },
    {
        "id": "逻辑推理",
        "question": """在一个房间里有三个人：Alice、Bob 和 Charlie。
其中一个人总是说真话，一个人总是说假话，一个人随机说真话或假话。

Alice 说："Bob 是说真话的人。"
Bob 说："Charlie 是说假话的人。"
Charlie 说："我不是随机说话的人。"

请问谁是说真话的人？""",
        "answer": "Charlie",
        "steps": """假设 Alice 说真话 → Bob 说真话 → 两个说真话的人，违反条件 → Alice 不说真话
假设 Alice 说假话 → Bob 不说真话 → Bob 可能是假话或随机
  - 如果 Bob 说假话 → "Charlie是说假话的人"是假的 → Charlie 不是说假话的人
    → Bob 是假话，Alice 可能随机或假话，Charlie 是真话或随机
  - Charlie 说"我不是随机" → 如果 Charlie 是真话者，这句话为真 → 他不是随机 ✓
  - 验证：Charlie 真话、Alice 假话、Bob 随机 — 检查各人陈述：
    - Alice(假): "Bob说真话" → 假 ✓ (Bob 是随机)
    - Bob(随机): "Charlie说假话" → 假/真都可能
    - Charlie(真): "我不是随机" → 真 ✓
  → Charlie 是说真话的人""",
    },
    {
        "id": "常识推理",
        "question": """以下哪种情况最可能导致一个城市公园的鸟类数量减少？

A) 公园附近新开了一家面包店
B) 公园里新增了 5 只流浪猫
C) 公园的喷泉被重新粉刷
D) 公园的长椅数量增加了一倍

请选出最可能的答案并解释。""",
        "answer": "B",
        "steps": """逐一分析每个选项：
A) 面包店 → 可能有食物残渣吸引鸟类，反而可能增加 → 不太可能
B) 流浪猫 → 猫是鸟类的天敌，会捕食鸟类 → 很可能导致数量减少
C) 喷泉重新粉刷 → 短期影响水质，但鸟类不依赖喷泉水生存 → 影响很小
D) 长椅增加 → 更多人类，可能造成干扰，但不如天敌的直接影响大 → 影响中等

综合判断：天敌（猫）对鸟类数量的威胁最大，B 是最可能的原因""",
    },
]

# ══════════════════════════════════════════════════════════════════════
# 实验 A：标准 Prompting（直接给答案）
# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("🔬 实验 A：标准 Prompting（不说'一步步想'）")
print("=" * 60)

STANDARD_SYSTEM = "你是一个有用的AI助手。请回答用户的问题。"

for p in problems:
    print(f"\n📋 {p['id']}")
    print(f"   问题: {p['question'][:50]}...")
    result = call_llm(STANDARD_SYSTEM, p["question"])
    # 截取结果的前 120 个字符展示
    short_result = result[:120].replace("\n", " ")
    print(f"   回答: {short_result}...")
    print(f"   正确答案: {p['answer']}")

# ══════════════════════════════════════════════════════════════════════
# 实验 B：Zero-shot CoT（加一句"Let's think step by step"）
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🔬 实验 B：Zero-shot CoT（加'让我们一步一步思考'）")
print("=" * 60)

COT_SYSTEM = "你是一个有用的AI助手。在回答任何问题之前，请先一步一步地思考。"

for p in problems:
    print(f"\n📋 {p['id']}")
    print(f"   问题: {p['question'][:50]}...")
    result = call_llm(COT_SYSTEM, p["question"])
    short_result = result[:120].replace("\n", " ")
    print(f"   回答: {short_result}...")
    print(f"   正确答案: {p['answer']}")

# ══════════════════════════════════════════════════════════════════════
# 实验 C：Few-shot CoT（给一个带推理步骤的示例，然后问新问题）
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🔬 实验 C：Few-shot CoT（给一个完整推理示例）")
print("=" * 60)

FEWSHOT_COT_SYSTEM = """你是一个有用的AI助手。回答问题时，请像下面的示例一样，展示完整的推理过程，然后给出最终答案。

示例问题：一个水池有两个水管，A管单独注满需要3小时，B管单独注满需要6小时。
如果两个水管同时开，需要多久注满水池？

示例回答：
1. A管每小时注水 1/3 池
2. B管每小时注水 1/6 池
3. 两管同时开，每小时注水 1/3 + 1/6 = 2/6 + 1/6 = 3/6 = 1/2 池
4. 注满需要 1 ÷ (1/2) = 2 小时
5. 答案：2 小时

请以相同的格式回答用户的问题。"""

for p in problems:
    print(f"\n📋 {p['id']}")
    print(f"   问题: {p['question'][:50]}...")
    result = call_llm(FEWSHOT_COT_SYSTEM, p["question"])
    short_result = result[:120].replace("\n", " ")
    print(f"   回答: {short_result}...")
    print(f"   正确答案: {p['answer']}")

# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🧠 观察引导")
print("=" * 60)
print("""
比较三组实验的答案：

实验 A（标准）— 嘴巴快，直接蹦答案
实验 B（Zero-shot CoT）— 加了"一步一步思考"，被迫慢下来
实验 C（Few-shot CoT）— 给了一个"推理→答案"的模板示例

观察三个问题：
1. 苹果问题：哪组实验算对了？
2. 逻辑问题：哪组实验的推理链条最清晰？
3. 常识问题：B（猫）是唯一正确答案，哪组答对了？

关键问题：
为什么只是加了一句"让我们一步一步思考"就能提升正确率？
这和上一节学的 In-Context Learning 有什么不同？
""")
