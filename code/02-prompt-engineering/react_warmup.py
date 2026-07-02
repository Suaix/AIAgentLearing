"""
模块 2 — Step 0 热身：ReAct Prompting
直观感受"推理 + 行动交替"和"纯推理"的本质区别

ReAct = Reasoning + Acting
模型不只是"想"，还能调用工具"做"——获取真实信息后再想，再行动

运行方式：
    cd code/02-prompt-engineering
    python react_warmup.py
"""

import os
import re
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


# ══════════════════════════════════════════════════════════════════════
# 模拟工具（本地执行，不需要网络）
# ══════════════════════════════════════════════════════════════════════

KNOWLEDGE_BASE = {
    "北京": {"人口": 2188, "面积": 16410, "简称": "京"},
    "上海": {"人口": 2487, "面积": 6340, "简称": "沪"},
    "深圳": {"人口": 1766, "面积": 1997, "简称": "深"},
    "广州": {"人口": 1882, "面积": 7434, "简称": "穗"},
    "杭州": {"人口": 1237, "面积": 16850, "简称": "杭"},
    "成都": {"人口": 2127, "面积": 14335, "简称": "蓉"},
    "东京": {"人口": 1396, "面积": 2194, "简称": None},
    "纽约": {"人口": 833, "面积": 1214, "简称": None},
    "伦敦": {"人口": 898, "面积": 1572, "简称": None},
}


def search_city(query: str) -> str:
    """模拟城市信息搜索工具"""
    query = query.strip()
    for city, info in KNOWLEDGE_BASE.items():
        if city in query:
            return f"{city}的信息：人口 {info['人口']} 万，面积 {info['面积']} km²，简称 {info['简称']}"
    return f"未找到「{query}」的信息"


def calculate(expression: str) -> str:
    """模拟计算器工具"""
    try:
        # 安全：只允许数字和基本运算符
        safe_expr = expression.strip()
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.\%]+$', safe_expr):
            return f"错误：表达式包含不允许的字符 —— {expression}"
        result = eval(safe_expr)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"


# ══════════════════════════════════════════════════════════════════════
# 任务定义
# ══════════════════════════════════════════════════════════════════════

TASKS = [
    {
        "id": "单步搜索",
        "question": "北京的人口是多少？上海呢？",
        "hint": "只需要查两次，不需要计算",
    },
    {
        "id": "搜索+计算",
        "question": "北京的人口是深圳人口的多少倍？（保留一位小数）",
        "hint": "需要先查两个城市的人口，然后做除法",
    },
    {
        "id": "多步搜索+计算",
        "question": "北京、上海、深圳三个城市的总人口是多少？平均每个城市多少人口？",
        "hint": "需要查三次，然后求和、求平均",
    },
]


# ══════════════════════════════════════════════════════════════════════
# 实验 A：标准 Prompt（无工具，纯靠模型训练数据回答）
# ══════════════════════════════════════════════════════════════════════
print("=" * 65)
print("🔬 实验 A：标准 Prompt（纯靠记忆，没有工具）")
print("=" * 65)

STANDARD_SYSTEM = "你是一个有用的AI助手。请直接回答用户的问题。"

for task in TASKS:
    print(f"\n📋 {task['id']}")
    print(f"   问题: {task['question']}")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": STANDARD_SYSTEM},
            {"role": "user", "content": task["question"]},
        ],
        temperature=0.0,
    )
    result = response.choices[0].message.content
    # 截取显示
    lines = result.strip().split("\n")
    for line in lines[:6]:
        print(f"   {line}")
    if len(lines) > 6:
        print(f"   ...（共 {len(lines)} 行）")
    print()


# ══════════════════════════════════════════════════════════════════════
# 实验 B：CoT Prompt（一步步推理，但还是没有工具）
# ══════════════════════════════════════════════════════════════════════
print("=" * 65)
print("🔬 实验 B：CoT Prompt（一步步推理，但没有工具）")
print("=" * 65)

COT_SYSTEM = "你是一个有用的AI助手。请一步一步思考后再回答用户的问题。"

for task in TASKS:
    print(f"\n📋 {task['id']}")
    print(f"   问题: {task['question']}")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": COT_SYSTEM},
            {"role": "user", "content": task["question"]},
        ],
        temperature=0.0,
    )
    result = response.choices[0].message.content
    lines = result.strip().split("\n")
    for line in lines[:6]:
        print(f"   {line}")
    if len(lines) > 6:
        print(f"   ...（共 {len(lines)} 行）")
    print()


# ══════════════════════════════════════════════════════════════════════
# 实验 C：ReAct Prompt（推理 + 行动交替，有工具！）
# ══════════════════════════════════════════════════════════════════════
print("=" * 65)
print("🔬 实验 C：ReAct Prompt（Thought → Action → Observation 循环）")
print("=" * 65)

REACT_SYSTEM = """你是一个能使用工具的AI助手。你的每次回复只能包含一轮 Thought + Action，然后等待工具返回 Observation。

重要：你绝对不能自己编造 Observation！工具结果由系统提供。

每次回复必须严格按以下格式：

Thought: [分析当前情况，我需要什么信息？]
Action: search_city[城市名]

或者：

Thought: [分析当前情况，我需要什么信息？]
Action: calculate[数学表达式]

或者（当你已经拿到所有需要的信息时）：

Thought: 我已经有足够信息回答
Final Answer: [最终答案]

规则：
- 每次回复只能包含一个 Action
- 绝对不能自己写 Observation（那不是真的工具结果！）
- Action 格式必须精确：search_city[北京] 或 calculate[2188 + 2487]
- 工具执行后你会收到 Observation，然后你再决定下一步"""

for task in TASKS:
    print(f"\n📋 {task['id']}")
    print(f"   问题: {task['question']}")
    print(f"   {'─' * 55}")

    messages = [
        {"role": "system", "content": REACT_SYSTEM},
        {"role": "user", "content": task["question"]},
    ]

    max_turns = 5  # 防止死循环
    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.0,
        )
        reply = response.choices[0].message.content

        # 把模型的回复加到消息历史
        messages.append({"role": "assistant", "content": reply})

        # 显示模型的思考过程
        for line in reply.strip().split("\n"):
            if line.startswith("Thought:"):
                print(f"   💭 {line}")
            elif line.startswith("Action:"):
                print(f"   🔧 {line}")
            elif line.startswith("Final Answer:"):
                print(f"   ✅ {line}")
            else:
                print(f"   {line}")

        # 先解析 Action 并执行（即使模型同时输出了 Final Answer）
        action_match = re.search(r"Action:\s*(search_city|calculate)\[(.+?)\]", reply)
        if action_match:
            tool_name = action_match.group(1)
            tool_input = action_match.group(2)
            if tool_name == "search_city":
                observation = search_city(tool_input)
            else:
                observation = calculate(tool_input)
            print(f"   📥 {observation}")
            # 把观察结果作为用户消息喂回
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue  # 继续下一轮

        # 没有 Action 但也没有 Final Answer——模型没按格式来
        if "Final Answer:" not in reply:
            print("   ⚠️  模型未按格式输出，提示重试...")
            messages.append({"role": "user", "content": "请按格式输出 Thought 和 Action，或给出 Final Answer。"})
            continue

        # 到达 Final Answer
        break
    print()


# ══════════════════════════════════════════════════════════════════════
# 对比总结
# ══════════════════════════════════════════════════════════════════════
print("=" * 65)
print("🧠 观察引导")
print("=" * 65)
print("""
比较三组实验的表现，思考以下问题：

1. 实验 A（标准 Prompt）和实验 B（CoT）的数据来源是什么？
   → 都是模型的训练记忆，可能过时或不准
   它们能查到"北京人口 2188 万"吗？（这是模拟数据，模型不可能知道）

2. 实验 C（ReAct）的数据来源是什么？
   → 工具返回的真实数据！模型不需要"记住"北京人口

3. ReAct 和 CoT 最本质的区别是什么？
   → CoT 只是在"想"，ReAct 是"想 → 做 → 看结果 → 继续想"
   → 多了 Action（调用工具）+ Observation（获取外部信息）

4. 这三个实验完美展示了 AI Agent 的核心模式：
   Standard  →  纯推理（脑子想）
   CoT       →  慢推理（一步步想，但还是脑子）
   ReAct     →  推理+行动（脑 + 手）← 这才是 Agent！
""")
