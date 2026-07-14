"""
模块 3：Tool Use / Function Calling — 子主题 2：单轮 vs 多轮调用 — Step 0 热身
================================================================================

本脚本演示 Tool Use 中"单轮"和"多轮"调用的核心区别：
  - 单轮（Single-turn）：LLM 一次性决定调哪些工具，不需要看结果再决定
  - 多轮（Multi-turn）：LLM 先调工具 A，看到结果后，再决定调工具 B

运行方式：
  uv run python code/03-tool-use/single_vs_multi_turn_warmup.py

四个演示用例：
  ① 单轮 × 1 工具   — "北京天气怎么样？"
  ② 单轮 × 2 并行工具 — "北京和上海天气分别怎么样？"
  ③ 多轮依赖链       — "杭州一日游：看天气 → 根据天气推荐室内/室外景点"
  ④ 多轮混合         — "北京到杭州多远+杭州天气 → 满足条件才查景点"
"""

import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# ---- 加载环境变量 ----
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
MODEL = "deepseek-v4-flash"

# ╔══════════════════════════════════════════════════════════════════╗
# ║  Part 0：模拟工具函数（Mock）                                   ║
# ╚══════════════════════════════════════════════════════════════════╝

def get_weather(city: str) -> str:
    """模拟天气查询（返回 JSON 字符串）"""
    weather_data = {
        "北京": {"天气": "晴", "温度": "28°C", "湿度": "35%"},
        "上海": {"天气": "阴", "温度": "25°C", "湿度": "70%"},
        "杭州": {"天气": "雨", "温度": "22°C", "湿度": "90%"},  # 故意设成雨，方便演示依赖链
        "深圳": {"天气": "晴", "温度": "32°C", "湿度": "60%"},
    }
    result = weather_data.get(city, {"天气": "未知", "温度": "N/A", "湿度": "N/A"})
    return json.dumps(result, ensure_ascii=False)


def get_attractions(city: str, type: str = "全部") -> str:
    """模拟景点查询（返回 JSON 字符串）"""
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
    """模拟距离查询（返回 JSON 字符串）"""
    distances = {
        ("北京", "杭州"): 1250,
        ("杭州", "北京"): 1250,
        ("北京", "上海"): 1200,
        ("上海", "北京"): 1200,
        ("上海", "杭州"): 175,
        ("杭州", "上海"): 175,
        ("北京", "深圳"): 2200,
        ("深圳", "北京"): 2200,
        ("上海", "深圳"): 1500,
        ("深圳", "上海"): 1500,
    }
    km = distances.get((from_city, to_city), 800)
    drive_hours = round(km / 100, 1)
    result = {
        "出发地": from_city,
        "目的地": to_city,
        "距离_km": km,
        "驾车约_小时": drive_hours,
    }
    return json.dumps(result, ensure_ascii=False)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Part 1：工具定义（三个工具，OpenAI 格式）                     ║
# ╚══════════════════════════════════════════════════════════════════╝

TOOLS = [
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
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_attractions",
            "description": "查询指定城市的旅游景点，可按类型筛选。当用户想了解某城市有什么好玩的地方时使用",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["室内", "室外", "全部"],
                        "description": "景点类型：'室内'适合雨天/高温天，'室外'适合好天气，'全部'返回所有景点",
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
                    "from_city": {
                        "type": "string",
                        "description": "出发城市名称",
                    },
                    "to_city": {
                        "type": "string",
                        "description": "目的城市名称",
                    },
                },
                "required": ["from_city", "to_city"],
            },
        },
    },
]

# 工具名 → 函数的映射
TOOL_MAP = {
    "get_weather": get_weather,
    "get_attractions": get_attractions,
    "get_distance": get_distance,
}


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Part 2：通用 Agent Loop 函数                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

def run_agent(user_query: str, max_turns: int = 5) -> None:
    """
    通用 Agent Loop：
    1. 将用户问题发给 LLM
    2. 如果 LLM 返回 tool_calls → 执行工具 → 把结果追加到消息历史 → 回到步骤 1
    3. 如果 LLM 返回纯文本 → 打印回答，结束

    这个函数本身不区分"单轮"还是"多轮"——循环次数完全由 LLM 的决策决定。
    """
    messages = [{"role": "user", "content": user_query}]
    total_tool_calls = 0

    for turn in range(1, max_turns + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message

        # ── 分支 1：LLM 决定调工具 ──
        if msg.tool_calls:
            num_calls = len(msg.tool_calls)
            total_tool_calls += num_calls

            if num_calls == 1:
                tc = msg.tool_calls[0]
                print(f"  [轮次 {turn}] 🔧 调用 1 个工具：{tc.function.name}")
            else:
                names = [tc.function.name for tc in msg.tool_calls]
                print(f"  [轮次 {turn}] 🔧 并行调用 {num_calls} 个工具：{names}")

            # 将 assistant 消息（含 tool_calls）加入历史
            messages.append(msg)

            # 执行每个工具，逐个追加 tool 结果消息
            for tc in msg.tool_calls:
                func = TOOL_MAP[tc.function.name]
                args = json.loads(tc.function.arguments)
                result = func(**args)
                print(f"    → {tc.function.name}({json.dumps(args, ensure_ascii=False)})")
                print(f"      结果：{result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            # 继续循环，让 LLM 看到结果后决定下一步
            continue

        # ── 分支 2：LLM 返回纯文本（无工具调用）→ 结束 ──
        print(f"\n📝 最终回答（共 {turn} 轮对话，{total_tool_calls} 次工具调用）：")
        print(f"   {msg.content}\n")
        break
    else:
        print("⚠️ 达到最大轮次上限，Agent 未给出最终回答")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Part 3：四个演示用例                                          ║
# ╚══════════════════════════════════════════════════════════════════╝

def main():
    print("=" * 65)
    print("  模块 3-2：单轮 vs 多轮 Tool 调用 — Step 0 热身运行")
    print("=" * 65)

    # ─── 演示 ①：单轮 × 1 工具 ───
    print("\n" + "─" * 65)
    print('  演示 ①：单轮 × 1 工具 — "北京今天天气怎么样？"')
    print("  预期：LLM 一次调用 get_weather → 看到结果 → 直接回答")
    print("─" * 65)
    run_agent("北京今天天气怎么样？")

    time.sleep(1)

    # ─── 演示 ②：单轮 × 2 并行工具 ───
    print("─" * 65)
    print('  演示 ②：单轮 × 2 并行工具 — "北京和上海天气分别怎么样？"')
    print("  预期：LLM 同时调用 get_weather(北京) + get_weather(上海) → 一起回答")
    print("─" * 65)
    run_agent("北京和上海天气分别怎么样？")

    time.sleep(1)

    # ─── 演示 ③：多轮依赖链 ───
    print("─" * 65)
    print('  演示 ③：多轮依赖链 — "帮我规划杭州一日游：先查天气，')
    print('           如果晴天推荐室外景点，雨天推荐室内景点"')
    print('  预期：轮1 get_weather(杭州) → 看到「雨」 → 轮2 get_attractions(杭州, 室内)')
    print("─" * 65)
    run_agent("帮我规划杭州一日游：先查天气，如果晴天推荐室外景点，如果雨天推荐室内景点。最后告诉我具体去哪些地方。")

    time.sleep(1)

    # ─── 演示 ④：多轮混合（并行 + 条件依赖）───
    print("─" * 65)
    print('  演示 ④：多轮混合 — "从北京到杭州多远？杭州天气如何？')
    print('           如果下雨且距离不到 1500 公里，推荐杭州室内景点"')
    print("  预期：轮1 并行 get_distance + get_weather")
    print("        → LLM 判断：距离<1500 且下雨 → 轮2 get_attractions(杭州, 室内)")
    print("─" * 65)
    run_agent(
        "从北京到杭州多远？杭州天气如何？"
        "如果杭州下雨而且距离不到1500公里的话，帮我推荐杭州的室内景点。"
    )

    print("=" * 65)
    print("  四个演示运行完毕。")
    print("  关键观察点：")
    print("  ① vs ②：同样是单轮，1 个工具 vs 2 个并行工具的区别")
    print("  ① vs ③：同样是查天气，为什么③需要多轮而①不需要？")
    print("  ③ vs ④：多轮中，什么决定了轮次数？")
    print("=" * 65)


if __name__ == "__main__":
    main()
