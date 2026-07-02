"""
模块 2 — Step 3 引导式修改：ReAct Prompting
4 个渐进任务：改参数 → 加工具 → 修 Bug → 扩展场景

运行方式：
    cd code/02-prompt-engineering
    python react_step3.py
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
# 共享工具 & 循环引擎（脚手架，已帮你写好）
# ══════════════════════════════════════════════════════════════════════

KNOWLEDGE_BASE = {
    "北京": {"人口": 2188, "面积": 16410, "简称": "京"},
    "上海": {"人口": 2487, "面积": 6340, "简称": "沪"},
    "深圳": {"人口": 1766, "面积": 1997, "简称": "深"},
    "广州": {"人口": 1882, "面积": 7434, "简称": "穗"},
    "杭州": {"人口": 1237, "面积": 16850, "简称": "杭"},
    "成都": {"人口": 2127, "面积": 14335, "简称": "蓉"},
}


def search_city(query: str) -> str:
    """模拟城市信息搜索工具（已写好）"""
    query = query.strip()
    for city, info in KNOWLEDGE_BASE.items():
        if city in query:
            return f"{city}：人口 {info['人口']} 万，面积 {info['面积']} km²"
    return f"未找到「{query}」的信息"


def calculate(expression: str) -> str:
    """模拟计算器工具（已写好）"""
    try:
        safe_expr = expression.strip()
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.\%]+$', safe_expr):
            return f"错误：表达式包含不允许的字符"
        result = eval(safe_expr)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"


def run_react_loop(system_prompt: str, question: str, max_turns: int = 5) -> None:
    """ReAct 循环引擎（脚手架，已写好）"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.0,
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        for line in reply.strip().split("\n"):
            prefix = line[:20]
            if "Thought:" in prefix:
                print(f"   💭 {line.strip()}")
            elif "Action:" in prefix:
                print(f"   🔧 {line.strip()}")
            elif "Final Answer:" in prefix:
                print(f"   ✅ {line.strip()}")

        action_match = re.search(r"Action:\s*(search_city|calculate)\[(.+?)\]", reply)
        if action_match:
            tool_name = action_match.group(1)
            tool_input = action_match.group(2)
            if tool_name == "search_city":
                observation = search_city(tool_input)
            else:
                observation = calculate(tool_input)
            print(f"   📥 {observation}")
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

        if "Final Answer:" not in reply:
            print("   ⚠️  格式错误，重试...")
            messages.append({"role": "user", "content": "请按格式输出。"})
            continue

        break


# ══════════════════════════════════════════════════════════════════════
# 基础 System Prompt（warmup 同款）
# ══════════════════════════════════════════════════════════════════════

BASE_REACT_PROMPT = """你是一个能使用工具的AI助手。你的每次回复只能包含一轮 Thought + Action，然后等待工具返回 Observation。

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


# ══════════════════════════════════════════════════════════════════════
# 任务 ①：改参数 —— 理解 max_turns 的含义
# ══════════════════════════════════════════════════════════════════════
print("=" * 65)
print("🔧 任务 ①：修改 max_turns —— 理解循环上限")
print("=" * 65)
print("""
max_turns 是 ReAct 循环的"安全阀"——超过这个轮数还没结束就强制终止。

实验 1：max_turns=5（默认）→ 让模型正常完成多步任务
实验 2：把 max_turns 改成 1 → 观察会发生什么

【你要做的】
在下面代码的 max_turns 参数位置，先保持 5 运行一次，再改成 1 运行一次，
对比两次输出的差别。

预测：max_turns=1 时模型能完成任务吗？为什么？
""")

input("按 Enter 运行实验 1（max_turns=5）...")

question = "北京、上海、深圳三个城市的总人口是多少？平均每个城市多少人口？"
print(f"\n📋 问题: {question}")
print(f"   max_turns = 5")
print(f"   {'─' * 55}")
run_react_loop(BASE_REACT_PROMPT, question, max_turns=5)

input("\n按 Enter 运行实验 2 —— 把上面的 max_turns 改成 1，观察结果...")

# 👆 你需要手动把下面这行的 max_turns=1 改成=5 先跑一次，再改回 1
print(f"\n📋 问题: {question}")
print(f"   max_turns = 1  ← 只给 1 轮！")
print(f"   {'─' * 55}")
run_react_loop(BASE_REACT_PROMPT, question, max_turns=1)

print("""
📊 思考：max_turns 设太小会怎样？设太大会怎样？实际项目中怎么选？""")


# ══════════════════════════════════════════════════════════════════════
# 任务 ②：加新工具 —— 添加天气查询功能
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("🔧 任务 ②：添加新工具 —— get_weather[]")
print("=" * 65)
print("""
现在你要给 ReAct Agent 添加一个新工具：天气查询。

给 Agent 加工具需要改 4 个地方（缺一不可）：
  ① 定义数据源（字典）
  ② 实现工具函数
  ③ 在 System Prompt 中声明新工具
  ④ 在循环引擎的正则和路由中添加新工具

下面 4 个位置标注了 TODO，请逐一填写。
""")

# ── TODO ①：补充天气数据 ──
# 请在字典中补充至少 3 个城市的天气信息（北京、上海、深圳）
# 格式参考：城市名 → 天气描述字符串
KNOWLEDGE_BASE_WEATHER = {
    # TODO: 在这里补充天气数据
    "北京": "晴，25°C，湿度 60%",
    "上海": "多云，22°C，湿度 70%",
    "深圳": "阵雨，24°C，湿度 65%"
}


# ── TODO ②：完成天气查询函数 ──
# 提示：参考 search_city() 的实现方式
# 从 KNOWLEDGE_BASE_WEATHER 中查找城市，返回格式化字符串
def get_weather(query: str) -> str:
    """TODO: 实现天气查询工具"""
    query = query.strip()
    for city, weather in KNOWLEDGE_BASE_WEATHER.items():
        if city in query:
            return f"{city} 的天气：{weather}"
    return f"未找到「{query}」的天气信息"


# ── TODO ③：修改 System Prompt（在工具列表中加入天气查询）──
# 提示：在 BASE_REACT_PROMPT 的基础上，找到 Action 格式说明部分，
#       添加 get_weather[城市名] 的用法说明
SYSTEM_PROMPT_WITH_WEATHER = """你是一个能使用工具的AI助手。你的每次回复只能包含一轮 Thought + Action，然后等待工具返回 Observation。

重要：你绝对不能自己编造 Observation！工具结果由系统提供。

你可以使用以下工具：
- search_city[城市名]：查询城市的人口和面积信息
- get_weather[城市名]：查询城市的天气信息
- calculate[数学表达式]：执行数学计算

每次回复必须严格按以下格式：

Thought: [分析当前情况，我需要什么信息？]
Action: search_city[城市名]

或者：

Thought: [分析当前情况，我需要什么信息？]
Action: get_weather[城市名]

或者：

Thought: [分析当前情况，我需要什么信息？]
Action: calculate[数学表达式]

或者（当你已经拿到所有需要的信息时）：

Thought: 我已经有足够信息回答
Final Answer: [最终答案]

规则：
- 每次回复只能包含一个 Action
- 绝对不能自己写 Observation（那不是真的工具结果！）
- 工具执行后你会收到 Observation，然后你再决定下一步"""


# ── TODO ④：增强 run_react_loop（支持 get_weather 工具）──
# 提示：需要改两处——正则表达式 + 路由分支（if/elif）
def run_react_loop_v2(system_prompt: str, question: str, max_turns: int = 5) -> None:
    """ReAct 循环引擎 v2 —— TODO：添加 get_weather 支持"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.0,
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        for line in reply.strip().split("\n"):
            prefix = line[:20]
            if "Thought:" in prefix:
                print(f"   💭 {line.strip()}")
            elif "Action:" in prefix:
                print(f"   🔧 {line.strip()}")
            elif "Final Answer:" in prefix:
                print(f"   ✅ {line.strip()}")

        # TODO: 修改正则表达式，让 get_weather 也能被匹配到
        # 当前正则：r"Action:\s*(search_city|calculate)\[(.+?)\]"
        action_match = re.search(
            r"Action:\s*(search_city|calculate|get_weather)\[(.+?)\]",  # ← TODO: 在这里加入 get_weather
            reply
        )
        if action_match:
            tool_name = action_match.group(1)
            tool_input = action_match.group(2)
            # TODO: 添加 get_weather 的路由分支
            if tool_name == "search_city":
                observation = search_city(tool_input)
            elif tool_name == "get_weather":
                observation = get_weather(tool_input)  # 假设函数已实现
            else:
                observation = calculate(tool_input)
            print(f"   📥 {observation}")
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

        if "Final Answer:" not in reply:
            print("   ⚠️  格式错误，重试...")
            messages.append({"role": "user", "content": "请按格式输出。"})
            continue

        break


# ── 测试天气查询 ──
input("\n完成 4 个 TODO 后，按 Enter 测试天气查询功能...")

print(f"\n📋 问题: 北京和深圳今天的天气分别怎么样？哪个城市更适合户外活动？")
print(f"   {'─' * 55}")
run_react_loop_v2(SYSTEM_PROMPT_WITH_WEATHER, "北京和深圳今天的天气分别怎么样？哪个城市更适合户外活动？")

print("""
✅ 验证标准：Agent 是否调用了 get_weather[北京] 和 get_weather[深圳]？
   是否基于天气数据给出了有依据的对比分析？""")


# ══════════════════════════════════════════════════════════════════════
# 任务 ③：修 Bug —— 正则表达式拼写错误导致工具调用静默失败
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("🔧 任务 ③：修 Bug —— 工具调用「静默失败」")
print("=" * 65)
print("""
下面的 run_react_loop_buggy 里故意埋了一个 Bug。

【现象】模型明明输出了 Action: search_city[北京]，格式完全正确，
       但工具就是没有被执行，一直在"格式错误，重试..."

【你要做的】
1. 先运行，观察现象
2. 对比 run_react_loop（正确的）和 run_react_loop_buggy（有 Bug 的），
   找出哪里不同
3. 修复它，让工具调用恢复正常

提示：仔细看正则表达式那行的拼写...
""")

input("按 Enter 运行有 Bug 的版本，观察现象...")


def run_react_loop_buggy(system_prompt: str, question: str, max_turns: int = 5) -> None:
    """有 Bug 的循环引擎 —— 能发现哪里不对劲吗？"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.0,
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        for line in reply.strip().split("\n"):
            prefix = line[:20]
            if "Thought:" in prefix:
                print(f"   💭 {line.strip()}")
            elif "Action:" in prefix:
                print(f"   🔧 {line.strip()}")
            elif "Final Answer:" in prefix:
                print(f"   ✅ {line.strip()}")

        # 🐛 BUG 在这里 —— 仔细看这行和上面正确版本的区别
        action_match = re.search(
            r"Action:\s*(search_city|calculate)\[(.+?)\]", reply
        )
        if action_match:
            tool_name = action_match.group(1)
            tool_input = action_match.group(2)
            if tool_name == "search_city":
                observation = search_city(tool_input)
            else:
                observation = calculate(tool_input)
            print(f"   📥 {observation}")
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

        if "Final Answer:" not in reply:
            print("   ⚠️  格式错误，重试...")
            messages.append({"role": "user", "content": "请按格式输出。"})
            continue

        break


print(f"\n📋 问题: 北京和上海哪个城市人口更多？")
print(f"   {'─' * 55}")
run_react_loop_buggy(BASE_REACT_PROMPT, "北京和上海哪个城市人口更多？")

print("""
🐛 找到 Bug 了吗？找到后修改上面标注的位置，重新运行验证修复。

提示：模型输出的 Action 是 search_city[北京]，但正则里写的是什么？""")


# ══════════════════════════════════════════════════════════════════════
# 任务 ④：扩展场景 —— 餐厅推荐 Agent（从模仿到迁移）
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("🔧 任务 ④：扩展场景 —— 餐厅推荐 Agent")
print("=" * 65)
print("""
你已经掌握了 ReAct Agent 的核心模式。现在把整套模式迁移到一个全新场景。

【场景】做一家本地生活 App 的餐厅推荐 Agent。
       用户问"推荐适合约会的川菜馆"或"附近有什么高评分的日料？"

【你需要完成】
1. 定义餐厅数据库 —— 至少 4 家，每家包含：name、cuisine、price、rating、tags
2. 实现 search_restaurant() 函数 —— 按菜系/名称/标签搜索
3. 写 SYSTEM_PROMPT_RESTAURANT —— 告诉模型它有哪些工具可用
4. 完成 run_react_loop_restaurant —— 支持 search_restaurant 的解析和路由

提示：直接复用前面写过的模式——改数据、改函数、改 Prompt、改路由。
""")

# ── TODO ①：定义餐厅数据库 ──
# 格式：每行一个字典，包含 name、cuisine（菜系）、price（人均）、rating（评分）、tags（标签列表）
RESTAURANT_DB = [
    # TODO: 在这里补充至少 4 家餐厅
    {"name": "蜀味轩", "cuisine": "川菜", "price": 85, "rating": 4.6, "tags": ["麻辣", "江湖菜"]},
    {"name": "和风居", "cuisine": "日料", "price": 120, "rating": 4.8, "tags": ["寿司", "约会"]},
    {"name": "意大利小馆", "cuisine": "意大利菜", "price": 95, "rating": 4.5, "tags": ["披萨", "浪漫"]},
    {"name": "静雅茶餐厅", "cuisine": "粤菜", "price": 70, "rating": 4.7, "tags": ["安静", "下午茶"]},
]


# ── TODO ②：实现餐厅搜索函数 ──
# 提示：遍历 RESTAURANT_DB，按 query 匹配菜系、名称或标签
# 返回清晰的格式化字符串，包含每家餐厅的名称、菜系、人均、评分、标签
def search_restaurant(query: str) -> str:
    """TODO: 实现餐厅搜索"""
    query = query.strip()
    for restaurant in RESTAURANT_DB:
        if (query in restaurant["name"] or
            query in restaurant["cuisine"] or
            any(query in tag for tag in restaurant["tags"])):
            return (f"{restaurant['name']}：{restaurant['cuisine']}，人均 {restaurant['price']} 元，"
                    f"评分 {restaurant['rating']}，标签 {', '.join(restaurant['tags'])}")
    return f"未找到匹配的餐厅"


# ── TODO ③：写 System Prompt ──
# 提示：参考 BASE_REACT_PROMPT，告诉模型它可以用 search_restaurant[关键词] 搜索
# 关键词可以是菜系名、特色标签（如"约会"、"安静"）
SYSTEM_PROMPT_RESTAURANT = """
你是一个餐厅推荐智能助手。你可以使用以下工具：
- search_restaurant[关键词]：按菜系、名称或标签搜索餐厅
每次回复必须严格按以下格式：
Thought: [分析当前情况，我需要什么信息？]
Action: search_restaurant[关键词]
或者（当你已经拿到所有需要的信息时）：
Thought: 我已经有足够信息回答
Final Answer: [最终答案]
规则：
- 每次回复只能包含一个 Action
- 绝对不能自己写 Observation（那不是真的工具结果！）
- 当有足够的信息或明确无法找到餐厅时，必须给出 Final Answer

"""


# ── TODO ④：完成循环引擎 ──
# 提示：参考 run_react_loop 的结构，把正则从 (search_city|calculate) 改成 (search_restaurant)，
#       把路由从 search_city/calculate 改成 search_restaurant
def run_react_loop_restaurant(system_prompt: str, question: str, max_turns: int = 5) -> None:
    """TODO: 餐厅推荐 Agent 循环 —— 请参考 run_react_loop 完成"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.0,
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        for line in reply.strip().split("\n"):
            prefix = line[:20]
            if "Thought:" in prefix:
                print(f"   💭 {line.strip()}")
            elif "Action:" in prefix:
                print(f"   🔧 {line.strip()}")
            elif "Final Answer:" in prefix:
                print(f"   ✅ {line.strip()}")

        # TODO: 修改正则表达式，匹配 search_restaurant[关键词]
        # TODO: 修改路由，调用 search_restaurant() 函数
        action_match = re.search(
            r"Action:\s*(search_restaurant)\[(.+?)\]", reply
        )
        if action_match:
            tool_name = action_match.group(1)
            tool_input = action_match.group(2)
            # TODO: 添加 search_restaurant 的路由
            if tool_name == "search_restaurant":
                observation = search_restaurant(tool_input)
            else:
                observation = f"未知工具 {tool_name}"
            print(f"   📥 {observation}")
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

        if "Final Answer:" not in reply:
            print("   ⚠️  格式错误，重试...")
            messages.append({"role": "user", "content": "请按格式输出。"})
            continue

        break


# ── 测试餐厅推荐 ──
input("\n完成 4 个 TODO 后，按 Enter 测试餐厅推荐 Agent...")

test_queries = [
    "推荐一个适合约会的餐厅",
    "我想吃川菜，有没有评分高的？",
]

for q in test_queries:
    print(f"\n📋 用户: {q}")
    print(f"   {'─' * 55}")
    run_react_loop_restaurant(SYSTEM_PROMPT_RESTAURANT, q)
    print()


# ══════════════════════════════════════════════════════════════════════
print("=" * 65)
print("🎯 Step 3 完成检查清单")
print("=" * 65)
print("""
□ 任务 ①：max_turns=1 时发生了什么？和 max_turns=5 差了几轮？
□ 任务 ②：get_weather[北京] 和 get_weather[深圳] 都成功调用了？
□ 任务 ③：找到正则里的拼写错误了吗？修复后重新运行，工具能正常调用了？
□ 任务 ④：餐厅推荐 Agent 能搜到餐厅并给出有理由的推荐吗？

全部完成 → 告诉我，进入 Step 4 费曼检验
""")
