"""
模块 3：Tool Use / Function Calling — 子主题 2：单轮 vs 多轮 — Step 3 引导式修改
=================================================================================

四个渐进式任务，通过命令行参数选择：
  uv run python code/03-tool-use/single_vs_multi_turn_step3.py 1    # 任务① 改参数
  uv run python code/03-tool-use/single_vs_multi_turn_step3.py 2    # 任务② 加功能
  uv run python code/03-tool-use/single_vs_multi_turn_step3.py 3    # 任务③ 修 bug
  uv run python code/03-tool-use/single_vs_multi_turn_step3.py 4    # 任务④ 扩展场景

基础架构来自 Step 0 热身代码，你需要完成各任务中的 TODO 部分。
"""

import os
import json
import sys
from xml.etree.ElementInclude import include
from dotenv import load_dotenv
from numpy import number
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
MODEL = "deepseek-v4-flash"


# ╔══════════════════════════════════════════════════════════════════╗
# ║  通用基础：Agent Loop（与 Step 0 warmup 相同的结构）          ║
# ╚══════════════════════════════════════════════════════════════════╝


def run_agent(user_query: str, tools: list, tool_map: dict, max_turns: int = 5) -> list:
    """
    通用 Agent Loop。

    参数：
        user_query: 用户问题
        tools: 工具定义列表
        tool_map: {"工具名": 函数} 的映射
        max_turns: 最大对话轮次（默认 5）

    返回：
        每轮信息的列表，格式为 [{"turn": N, "tool_calls": [...], "results": [...]}, ...]
    """
    messages = [{"role": "user", "content": user_query}]
    turn_log = []

    for turn in range(1, max_turns + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message

        # LLM 决定调工具
        if msg.tool_calls:
            log_entry = {"turn": turn, "tool_calls": [], "results": []}
            for tc in msg.tool_calls:
                func = tool_map[tc.function.name]
                args = json.loads(tc.function.arguments)
                result = func(**args)
                log_entry["tool_calls"].append({"name": tc.function.name, "args": args})
                log_entry["results"].append(result)
                print(
                    f"  [轮次 {turn}] {tc.function.name}({json.dumps(args, ensure_ascii=False)}) → {result}"
                )
            turn_log.append(log_entry)

            messages.append(msg)
            for tc in msg.tool_calls:
                func = tool_map[tc.function.name]
                args = json.loads(tc.function.arguments)
                result = func(**args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )
            continue

        # LLM 返回纯文本 → 结束
        print(f"\n📝 最终回答（共 {turn} 轮）：")
        print(f"   {msg.content}\n")
        turn_log.append({"turn": turn, "final_answer": msg.content})
        break
    else:
        print(f"⚠️ 达到 max_turns={max_turns} 上限，Agent 循环被截断！")
        turn_log.append({"turn": max_turns, "truncated": True})

    return turn_log


# ╔══════════════════════════════════════════════════════════════════╗
# ║  共享 Mock 工具函数                                           ║
# ╚══════════════════════════════════════════════════════════════════╝


def get_weather(city: str) -> str:
    """模拟天气查询"""
    weather_data = {
        "北京": {"天气": "晴", "温度": "28°C", "湿度": "35%"},
        "上海": {"天气": "阴", "温度": "25°C", "湿度": "70%"},
        "杭州": {"天气": "雨", "温度": "22°C", "湿度": "90%"},
        "深圳": {"天气": "晴", "温度": "32°C", "湿度": "60%"},
        "成都": {"天气": "阴", "温度": "24°C", "湿度": "75%"},
    }
    result = weather_data.get(city, {"天气": "未知", "温度": "N/A", "湿度": "N/A"})
    return json.dumps(result, ensure_ascii=False)


def get_attractions(city: str, type: str = "全部") -> str:
    """模拟景点查询"""
    attractions = {
        "杭州": {
            "室外": ["西湖", "灵隐寺", "龙井茶园", "九溪十八涧"],
            "室内": ["杭州博物馆", "丝绸博物馆", "南宋官窑博物馆", "万象城购物中心"],
        },
        "北京": {
            "室外": ["故宫", "长城", "颐和园", "天坛"],
            "室内": ["国家博物馆", "中国科技馆", "798 艺术区", "三里屯太古里"],
        },
        "上海": {
            "室外": ["外滩", "豫园", "迪士尼乐园", "世纪公园"],
            "室内": ["上海博物馆", "上海科技馆", "南京路步行街", "环球金融中心"],
        },
    }
    city_data = attractions.get(city, {})
    if type == "全部":
        result = city_data
    else:
        result = city_data.get(type, [])
    return json.dumps(result, ensure_ascii=False)


def get_distance(from_city: str, to_city: str) -> str:
    """模拟距离查询"""
    distances = {
        ("北京", "杭州"): 1250,
        ("杭州", "北京"): 1250,
        ("北京", "上海"): 1200,
        ("上海", "北京"): 1200,
        ("上海", "杭州"): 175,
        ("杭州", "上海"): 175,
    }
    km = distances.get((from_city, to_city), 800)
    result = {
        "出发地": from_city,
        "目的地": to_city,
        "距离_km": km,
        "驾车约_小时": round(km / 100, 1),
    }
    return json.dumps(result, ensure_ascii=False)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  共享工具定义（与 warmup 相同的三个基础工具）                 ║
# ╚══════════════════════════════════════════════════════════════════╝

BASE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气状况，返回天气、温度、湿度",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'、'杭州'",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_attractions",
            "description": "查询指定城市的旅游景点，可按类型筛选。type='室内'适合雨天，type='室外'适合晴天，type='全部'返回所有",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "type": {
                        "type": "string",
                        "enum": ["室内", "室外", "全部"],
                        "description": "景点类型",
                        "default": "全部",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_distance",
            "description": "查询两个城市之间的驾车距离和预计时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_city": {"type": "string", "description": "出发城市"},
                    "to_city": {"type": "string", "description": "目的城市"},
                },
                "required": ["from_city", "to_city"],
            },
        },
    },
]

BASE_TOOL_MAP = {
    "get_weather": get_weather,
    "get_attractions": get_attractions,
    "get_distance": get_distance,
}


# ╔══════════════════════════════════════════════════════════════════╗
# ║  任务 ①：改参数 — max_turns 对多轮调用完整性的影响           ║
# ╚══════════════════════════════════════════════════════════════════╝


def task1():
    """
    任务 ①：修改 max_turns，观察多轮调用链被截断

    目标：
      理解 max_turns 参数如何影响多轮调用的完整性。
      当 max_turns 不足以覆盖所有必需的轮次时，Agent 会"半途而废"。

    实验：
      同一个多轮问题（杭州一日游：天气 → 景点），分别用 max_turns=1 和 max_turns=3 运行。
      观察两者的输出差异。

    你的任务：
      ① 运行代码，观察 max_turns=1 时的截断现象
      ② 修改下面 TODO 标记的 max_turns 值，观察不同取值的效果
      ③ 回答：这个多轮场景至少需要 max_turns 等于多少？为什么？
    """
    print("=" * 60)
    print("  任务 ①：改参数 — max_turns 对多轮调用完整性的影响")
    print("=" * 60)

    query = (
        "帮我规划杭州一日游：先查天气，"
        "如果晴天推荐室外景点，如果雨天推荐室内景点。"
        "最后告诉我具体去哪里。"
    )

    # ── 实验 A：max_turns=1（截断）──
    print("\n── 实验 A：max_turns = 1 ──")
    print("  预期：第一轮调了 get_weather 后，没有第二轮来调 get_attractions")
    # TODO: 修改下面的 max_turns 值为 1
    print("  [运行中...]")
    run_agent(query, tools=BASE_TOOLS, tool_map=BASE_TOOL_MAP, max_turns=1)

    # ── 实验 B：max_turns=3（正常完成）──
    print("\n── 实验 B：max_turns = 3 ──")
    print("  预期：有足够的轮次完成 天气 → 景点 的完整链")
    # TODO: 修改下面的 max_turns 值为 3
    print("  [运行中...]")
    run_agent(query, tools=BASE_TOOLS, tool_map=BASE_TOOL_MAP, max_turns=3)

    # ── 实验 C：你来探索 ──
    print("\n── 实验 C：你的探索 ──")
    print("  试试看 max_turns = ? 效果如何？")
    # TODO: 尝试不同的 max_turns 值，看看什么值刚好够、什么值浪费
    # 提示：这个多轮场景"至少"需要多少轮？用你的值替换 ?
    # TODO: 修改下面的 max_turns 值为你猜测的值
    # print("  [运行中...]")
    run_agent(query, tools=BASE_TOOLS, tool_map=BASE_TOOL_MAP, max_turns=4)

    # ── 思考题 ──
    print("\n💡 思考：")
    print("  ① max_turns=1 时，LLM 调了 get_weather 之后发生了什么？")
    print("  ② 这个多轮场景最少需要 max_turns 等于多少？为什么？")
    print("  ③ 如果把 max_turns 设得过大（比如 20），有什么坏处？")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  任务 ②：加功能 — 新增餐厅推荐工具，构建三轮依赖链          ║
# ╚══════════════════════════════════════════════════════════════════╝


def task2():
    """
    任务 ②：新增 get_restaurants 工具，让旅行规划从两轮扩展到三轮

    目标：
      在现有旅行助手基础上，添加餐厅查询功能。
      构建"天气 → 景点 → 餐厅"三轮依赖链。

    场景：
      "帮我规划杭州一日游：先查天气 → 根据天气推荐景点 → 再推荐景点附近餐厅"

    你需要完成 3 个 TODO：
      TODO-2A：实现 get_restaurants 的 mock 函数
      TODO-2B：定义 get_restaurants 工具的 JSON Schema
      TODO-2C：将新工具注册到 TOOL_MAP 和 TOOLS 列表

    参考格式：参见上方 BASE_TOOLS 中已有的三个工具定义
    """

    print("=" * 60)
    print("  任务 ②：加功能 — 新增餐厅推荐，构建三轮依赖链")
    print("=" * 60)

    # ── TODO-2A：实现 get_restaurants mock 函数 ──
    # 参数：
    #   city (str): 城市名称
    #   near_attraction (str, 可选): 靠近哪个景点，默认 None 表示不限位置
    # 返回：
    #   JSON 字符串，格式如：
    #   [{"name": "楼外楼", "cuisine": "杭帮菜", "price": "人均150元", "near": "西湖"},
    #    {"name": "外婆家", "cuisine": "杭帮菜", "price": "人均80元", "near": "杭州博物馆"}, ...]
    # 提示：为至少 2 个城市准备数据（杭州、北京），每个城市至少 4 家餐厅

    # TODO: 你的代码 — 实现 get_restaurants(city, near_attraction=None) 函数
    def get_restaurants(city: str, near_attraction: str | None = None) -> str:
        restaurants_db = {
            "杭州": [
                {
                    "name": "楼外楼",
                    "cuisine": "杭帮菜",
                    "price": "人均150元",
                    "near": "西湖",
                },
                {
                    "name": "外婆家",
                    "cuisine": "杭帮菜",
                    "price": "人均80元",
                    "near": "杭州博物馆",
                },
                {
                    "name": "费大厨",
                    "cuisine": "川菜",
                    "price": "人均100元",
                    "near": "万象城购物中心",
                },
                {
                    "name": "麦当劳",
                    "cuisine": "快餐",
                    "price": "人均50元",
                    "near": "万象城购物中心",
                },
            ],
            "北京": [
                {
                    "name": "便宜坊",
                    "cuisine": "北京菜",
                    "price": "人均180元",
                    "near": "故宫博物院",
                },
                {
                    "name": "金掌勺",
                    "cuisine": "东北菜",
                    "price": "人均60元",
                    "near": "后海",
                },
                {
                    "name": "绿茶餐厅",
                    "cuisine": "川菜",
                    "price": "人均160元",
                    "near": "798 艺术区",
                },
                {
                    "name": "门框卤煮",
                    "cuisine": "北京菜",
                    "price": "人均20元",
                    "near": "颐和园",
                },
            ],
        }
        result = []
        restaurants_by_city = restaurants_db.get(city, [])
        if near_attraction and len(restaurants_by_city) > 0:
            for restaurant in restaurants_by_city:
                if near_attraction in restaurant["near"]:
                    result.append(restaurant)
        else:
            # 没有指定附近景区
            result = restaurants_by_city
        return json.dumps({city: result}, ensure_ascii=False)

    # ── TODO-2B：定义 get_restaurants 工具的 JSON Schema ──
    # 参考上方 BASE_TOOLS 中 get_attractions 的格式
    # 关键字段：
    #   - name: "get_restaurants"
    #   - description: 清晰描述工具的用途和何时使用
    #   - parameters.city: string 类型，城市名称
    #   - parameters.near_attraction: string 类型，可选参数，用于按景点位置筛选

    # TODO: 你的代码 — 定义 get_restaurants 工具的 JSON Schema
    restaurant_tool = {
        "type": "function",
        "function": {
            "name": "get_restaurants",
            "description": "查询指定城市下某个景区附近的饭店信息，返回饭店名称、菜系、人均消费和在哪个景区附近。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名，如：北京、杭州等",
                    },
                    "near_attraction": {
                        "type": "string",
                        "description": "景点名称",
                    },
                },
                "required": ["city"],
            },
        },
    }

    # ── TODO-2C：注册新工具 ──
    # 将 get_restaurants 加入到 tools 列表和 tool_map 字典

    # TODO: 你的代码 — 构建扩展后的 tools 和 tool_map
    # extended_tools = BASE_TOOLS + [...]   # 加入你的新工具
    # extended_tool_map = {**BASE_TOOL_MAP, "get_restaurants": get_restaurants}

    extended_tools = BASE_TOOLS + [
        restaurant_tool
    ]  # TODO: 替换 —— 加上 restaurant_tool
    extended_tool_map = {**BASE_TOOL_MAP, "get_restaurants": get_restaurants}

    # ── 运行测试 ──
    query = (
        "帮我规划杭州一日游：先查天气，如果晴天推荐室外景点、如果雨天推荐室内景点。"
        "然后根据推荐的第一个景点，帮我找附近的餐厅。"
    )
    print(f"\n  用户问题：{query}\n")
    # TODO: 取消下面的注释来运行测试
    run_agent(query, tools=extended_tools, tool_map=extended_tool_map, max_turns=4)

    print("\n💡 思考：")
    print("  ① 这个场景一共需要几轮对话？每轮做了什么？")
    print("  ② 如果 LLM 在第一轮同时调了 get_weather 和 get_attractions，")
    print("     为什么这是不合理的？（提示：景点类型依赖天气）")
    print("  ③ get_restaurants 的 near_attraction 参数为什么要设计成可选的？")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  任务 ③：修 bug — 工具返回数据不完整，导致多轮决策失败       ║
# ╚══════════════════════════════════════════════════════════════════╝


def task3():
    """
    任务 ③：修复一个导致多轮调用链断裂的 bug

    问题描述：
      在旅行规划场景中，用户查询成都一日游。LLM 调了 get_weather("成都")，
      但返回的数据缺少关键字段。LLM 无法判断是晴天还是雨天，
      导致后续 get_attractions 不知道该传 type="室内" 还是 type="室外"。

    bug 定位：
      查看下方 get_weather_buggy 函数的实现，
      找出为什么对"成都"返回的数据会导致多轮链断裂。

    你的任务：
      TODO-3A：运行 buggy 版本，观察 LLM 在轮 2 的表现
      TODO-3B：找到并修复 get_weather_buggy 中"成都"数据的 bug
      TODO-3C：验证修复后三轮链正常完成
    """

    print("=" * 60)
    print("  任务 ③：修 bug — 不完整的工具返回导致多轮断裂")
    print("=" * 60)

    # ── Buggy 版本的天气函数 ──
    def get_weather_buggy(city: str) -> str:
        """模拟天气查询 —— 包含一个 bug"""
        weather_data = {
            "北京": {"天气": "晴", "温度": "28°C", "湿度": "35%"},
            "上海": {"天气": "阴", "温度": "25°C", "湿度": "70%"},
            "杭州": {"天气": "雨", "温度": "22°C", "湿度": "90%"},
            # 成都的数据有 bug —— 缺少关键字段
            "成都": {"天气": "雨", "温度": "24°C", "湿度": "75%"},
        }
        result = weather_data.get(city, {"天气": "未知", "温度": "N/A", "湿度": "N/A"})
        return json.dumps(result, ensure_ascii=False)

    buggy_tool_map = {
        "get_weather": get_weather_buggy,  # ← 用的是 buggy 版本
        "get_attractions": get_attractions,
        "get_distance": get_distance,
    }

    # ── TODO-3A：运行 buggy 版本，观察现象 ──
    query = (
        "帮我规划成都一日游：先查天气，"
        "如果晴天推荐室外景点，如果雨天推荐室内景点。"
        "最后告诉我具体去哪里。"
    )
    print(f"\n  用户问题：{query}")
    print("\n  ── Buggy 版本运行 ──")
    print("  预期：轮 1 调 get_weather('成都')，但返回数据不完整")
    print("        轮 2 LLM 可能跳过条件判断，直接调 get_attractions(type='全部')")
    print("        或者 LLM 直接基于不完整数据给出模糊回答\n")
    # TODO: 取消下面的注释来观察 bug 效果
    # run_agent(query, tools=BASE_TOOLS, tool_map=buggy_tool_map, max_turns=3)

    # ── TODO-3B：修复 bug ──
    print("\n  ── 修复 bug ──")
    print("  在下方修复 get_weather_buggy 中成都的数据，补充缺少的字段。")
    print("  提示：成都的天气是'阴'天。\n")

    # TODO: 你的代码 — 修复 get_weather_buggy 中"成都"的数据
    # 修复方式 1：直接修改上面 weather_data 字典中"成都"的值
    # 修复方式 2：在这里重新定义完整的 weather_data，然后用它替换
    # 提示：确保返回的 JSON 包含 "天气"、"温度"、"湿度" 三个字段

    # ── TODO-3C：验证修复 ──
    print("\n  ── 验证修复 ──")
    print("  用你修复后的版本重新运行，确认：")
    print("    ① 轮 1 get_weather('成都') 返回了包含'天气'字段的完整数据")
    print("    ② 轮 2 LLM 能正确判断天气并调用 get_attractions(type='室内'/'室外')")
    print("    ③ 最终给出了明确的景点推荐\n")
    # TODO: 修复后取消注释来验证
    run_agent(query, tools=BASE_TOOLS, tool_map=buggy_tool_map, max_turns=3)

    print("\n💡 思考：")
    print("  ① 为什么缺少一个字段就能让整个多轮链断裂？")
    print("  ② 在实际生产环境中，如果第三方 API 返回了不完整的数据，")
    print(
        "     你应该在哪个环节做防御？（三个选项：工具函数内 / Agent Loop 中 / 让 LLM 自己处理）"
    )


# ╔══════════════════════════════════════════════════════════════════╗
# ║  任务 ④：扩展场景 — 电商购物助手（全新工具集 + 决策链）     ║
# ╚══════════════════════════════════════════════════════════════════╝


def task4():
    """
    任务 ④：为电商购物助手构建全新的工具集和多轮决策链

    场景：
      用户想买一件商品，需要经历"查库存 → 查价格 → 查余额 → 判断能不能买"的决策链。
      其中"查库存"和"查价格"可以并行（互相独立），
      但"查余额"必须等价格出来后才能判断够不够。

    你需要完成 3 个 TODO：
      TODO-4A：实现三个 mock 函数（check_stock, get_price, check_balance）
      TODO-4B：定义三个工具的 JSON Schema
      TODO-4C：组装工具和 tool_map，编写测试查询

    工具说明：
      check_stock(product_name)  → 返回 {"in_stock": true/false, "quantity": N}
      get_price(product_name)    → 返回 {"product": "...", "price": N, "currency": "CNY"}
      check_balance()            → 返回 {"balance": N, "currency": "CNY"}
    """

    print("=" * 60)
    print("  任务 ④：扩展场景 — 电商购物助手")
    print("=" * 60)

    # ── TODO-4A：实现三个 mock 函数 ──
    # 提示：
    #   check_stock: 为 iPhone 16 返回有货 (quantity: 15)，为 RTX 5090 返回无货
    #   get_price: iPhone 16 → 6999元，RTX 5090 → 14999元
    #   check_balance: 当前账户余额 8000 元

    # TODO: 你的代码 — 实现 check_stock(product_name) 函数
    PRODUCT_DB = {
        "iPhone 16": {
            "name": "iPhone 16",
            "quantity": 15,
            "price": 6999,
            "desc": "苹果16最新手机",
        },
        "RTX 5090": {"name": "RTX 5090", "quantity": 0, "price": 14999},
    }

    def check_stock(product_name: str) -> str:
        product = PRODUCT_DB.get(
            product_name, {"name": "N/A", "quantity": 0, "price": "N/A", "desc": "N/A"}
        )
        return json.dumps({"quantity": product["quantity"]}, ensure_ascii=False)

    # TODO: 你的代码 — 实现 get_price(product_name) 函数
    def get_price(product_name: str) -> str:
        product = PRODUCT_DB.get(
            product_name, {"name": "N/A", "quantity": 0, "price": "N/A", "desc": "N/A"}
        )
        return json.dumps({"price": product["price"]}, ensure_ascii=False)

    # TODO: 你的代码 — 实现 check_balance() 函数
    def check_balance() -> str:
        return "8000"

    # ── TODO-4B：定义三个工具的 JSON Schema ──
    # 参考 BASE_TOOLS 的格式，为三个电商工具各写一份定义
    # 关键：description 要能让 LLM 准确理解何时调用

    # TODO: 你的代码 — 定义 check_stock 工具的 JSON Schema
    stock_tool = {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "根据商品名称查询商品库存，返回该商品的库存信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "商品名称，如iPhone 16, RTX 5090等",
                    },
                },
                "required": ["product_name"],
            },
        },
    }

    # TODO: 你的代码 — 定义 get_price 工具的 JSON Schema
    price_tool = {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "根据商品名称查询商品价格，单位为元。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "商品名称，如iPhone 16, RTX 5090等",
                    },
                },
                "required": ["product_name"],
            },
        },
    }

    # TODO: 你的代码 — 定义 check_balance 工具的 JSON Schema
    balance_tool = {
        "type": "function",
        "function": {
            "name": "check_balance",
            "description": "查询自己当前的账户余额，单位为元；",
        },
    }

    # ── TODO-4C：组装工具集，编写测试查询 ──
    # 将所有工具放入 shop_tools 列表，所有函数注册到 shop_tool_map
    # 然后构造一个合适的查询，验证多轮决策链

    shop_tools = [stock_tool, price_tool, balance_tool]
    shop_tool_map = {
        "check_stock": check_stock,
        "get_price": get_price,
        "check_balance": check_balance,
    }
    # shop_tools = []  # TODO: 替换
    # shop_tool_map = {}  # TODO: 替换

    # TODO: 编写测试查询
    # 要求：
    #   1. 让 LLM 先并行查库存+价格（互不依赖）
    #   2. 然后查余额（依赖价格）
    #   3. 最后给出"能买"或"买不起"的结论
    shop_query = "我想买 iPhone 16，帮我查一下当前是否有货以及价格是多少，如果有货且查询到单价了，再检查下我当前的账户余额是否可以买的起，回复：'能买'或'买不起'即可"  # TODO: 完善这个查询

    print("\n  📋 请完成以上 TODO 后取消注释运行：")
    # print(f"\n  用户问题：{shop_query}\n")
    run_agent(shop_query, tools=shop_tools, tool_map=shop_tool_map, max_turns=4)

    print("\n💡 思考：")
    print("  ① 在你的实现中，LLM 能否正确识别 check_stock 和 get_price 可以并行？")
    print("  ② check_balance 为什么必须排在 get_price 之后？")
    print("  ③ 如果 check_stock 返回 out_of_stock，LLM 还应该继续调 get_price 吗？")
    print("     你的查询语句如何引导 LLM 做这个判断？")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  入口：命令行参数分发                                         ║
# ╚══════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请指定任务编号：")
        print("  uv run python code/03-tool-use/single_vs_multi_turn_step3.py 1")
        print("  uv run python code/03-tool-use/single_vs_multi_turn_step3.py 2")
        print("  uv run python code/03-tool-use/single_vs_multi_turn_step3.py 3")
        print("  uv run python code/03-tool-use/single_vs_multi_turn_step3.py 4")
        sys.exit(1)

    task_num = sys.argv[1]
    tasks = {"1": task1, "2": task2, "3": task3, "4": task4}

    if task_num not in tasks:
        print(f"未知任务编号：{task_num}，请输入 1-4")
        sys.exit(1)

    tasks[task_num]()
