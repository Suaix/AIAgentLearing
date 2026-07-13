"""
模块 3：Tool Use / Function Calling — Step 0 热身运行
=====================================================

这个脚本演示了 Tool Use 的完整流程：
  1. 定义工具（JSON Schema）
  2. 模型决定调用哪个工具
  3. 执行工具函数
  4. 将结果返回给模型
  5. 模型生成最终回答

运行方式：
  uv run python code/03-tool-use/tool_definition_warmup.py

三个演示场景：
  ① 单工具调用 — 计算器（模型自动选择正确的运算）
  ② 单工具调用 — 天气查询（模拟 API）
  ③ 多轮工具调用 — 先查天气再判断是否需要带伞
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# ---- 加载环境变量 ----
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
MODEL = "deepseek-v4-flash"  # 快速模型，适合调试

# ╔══════════════════════════════════════════════════════════════╗
# ║  Part 0：工具定义 — 用 JSON Schema 描述工具"长什么样"       ║
# ╚══════════════════════════════════════════════════════════════╝

# 工具 1：计算器
calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "执行基本数学运算：加法、减法、乘法、除法",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "要执行的运算类型",
                },
                "a": {
                    "type": "number",
                    "description": "第一个操作数",
                },
                "b": {
                    "type": "number",
                    "description": "第二个操作数",
                },
            },
            "required": ["operation", "a", "b"],
        },
    },
}

# 工具 2：天气查询（模拟）
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的实时天气信息。返回温度、湿度、天气状况。",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如 'Beijing', 'Shanghai', 'Tokyo'",
                },
            },
            "required": ["city"],
        },
    },
}

# 工具注册表：将所有可用工具放在一个列表里
AVAILABLE_TOOLS = [calculator_tool, weather_tool]


# ╔══════════════════════════════════════════════════════════════╗
# ║  Part 1：工具执行器 — 真正干活的函数                        ║
# ╚══════════════════════════════════════════════════════════════╝

def execute_calculator(operation: str, a: float, b: float) -> dict:
    """执行数学计算"""
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return {"error": "除数不能为零"}
        result = a / b
    else:
        return {"error": f"未知运算: {operation}"}

    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": result,
    }


def execute_get_weather(city: str) -> dict:
    """模拟天气查询（实际项目中这里应该调用真实天气 API）"""
    # 模拟数据 — 实际项目中替换为 API 调用
    weather_db = {
        "beijing": {"temperature": 28, "humidity": 65, "condition": "晴天", "wind": "北风 3级"},
        "shanghai": {"temperature": 32, "humidity": 80, "condition": "多云转阵雨", "wind": "东南风 4级"},
        "tokyo": {"temperature": 25, "humidity": 70, "condition": "小雨", "wind": "东风 2级"},
        "shenzhen": {"temperature": 33, "humidity": 85, "condition": "雷阵雨", "wind": "南风 5级"},
    }

    city_lower = city.lower()
    if city_lower in weather_db:
        return {"city": city, **weather_db[city_lower]}
    else:
        return {"city": city, "error": f"暂无 '{city}' 的天气数据（模拟数据库仅包含 Beijing/Shanghai/Tokyo/Shenzhen）"}


def execute_tool(tool_name: str, arguments: dict) -> str:
    """
    根据 tool_name 分发到对应的执行函数。
    返回 JSON 字符串（这是 LLM 要求的格式）。
    """
    if tool_name == "calculator":
        result = execute_calculator(**arguments)
    elif tool_name == "get_weather":
        result = execute_get_weather(**arguments)
    else:
        result = {"error": f"未知工具: {tool_name}"}

    return json.dumps(result, ensure_ascii=False)


# ╔══════════════════════════════════════════════════════════════╗
# ║  Part 2：核心循环 — LLM 与工具的交互                        ║
# ╚══════════════════════════════════════════════════════════════╝

def run_agent(user_query: str, verbose: bool = True) -> str:
    """
    Agent 核心循环：
      1. 发送用户问题 + 工具定义给 LLM
      2. 如果 LLM 返回 tool_calls → 执行工具 → 把结果追加到对话
      3. 循环直到 LLM 返回纯文本回答
    """
    messages = [{"role": "user", "content": user_query}]

    max_turns = 5  # 安全上限，防止无限循环
    for turn in range(max_turns):
        if verbose:
            print(f"\n{'─'*60}")
            print(f"🔄 第 {turn + 1} 轮调用 LLM...")

        # 调用 LLM，带上工具定义
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=AVAILABLE_TOOLS,
            temperature=0.1,  # 低温度 → 更稳定的工具选择
        )

        assistant_message = response.choices[0].message

        # 情况 A：LLM 想调用工具
        if assistant_message.tool_calls:
            print(f"   🤖 LLM 决定调用 {len(assistant_message.tool_calls)} 个工具")

            # 先把 assistant 消息（含 tool_calls）加入对话历史
            messages.append(assistant_message.model_dump())

            for tc in assistant_message.tool_calls:
                tool_name = tc.function.name
                arguments = json.loads(tc.function.arguments)

                print(f"   🔧 调用工具: {tool_name}")
                print(f"      📥 参数: {json.dumps(arguments, ensure_ascii=False)}")

                # 执行工具
                tool_result = execute_tool(tool_name, arguments)
                print(f"      📤 结果: {tool_result}")

                # 将工具执行结果作为 tool 消息加入对话历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result,
                })

            # 继续循环，让 LLM 看到工具结果后决定下一步
            continue

        # 情况 B：LLM 返回纯文本回答（对话结束）
        final_answer = assistant_message.content
        if verbose:
            print(f"   💬 LLM 最终回答: {final_answer}")
        return final_answer

    return "⚠️ 达到最大轮次上限，对话未正常结束"


# ╔══════════════════════════════════════════════════════════════╗
# ║  Part 3：三个演示场景                                        ║
# ╚══════════════════════════════════════════════════════════════╝

def demo1_calculator():
    """演示①：单工具调用 — 计算器"""
    print("\n" + "=" * 60)
    print("📐 演示①：计算器工具 — 模型自动选择运算类型")
    print("=" * 60)

    queries = [
        "请帮我计算 156 乘以 23 等于多少？",
        "把 1000 除以 3，精确计算结果。",
        "158 + 497 等于多少？然后再减去 200。",
    ]

    for query in queries:
        print(f"\n👤 用户: {query}")
        answer = run_agent(query, verbose=True)
        print(f"✅ 最终回答: {answer}")


def demo2_weather():
    """演示②：单工具调用 — 天气查询"""
    print("\n" + "=" * 60)
    print("🌤️ 演示②：天气查询工具 — 模拟 API 调用")
    print("=" * 60)

    query = "北京和上海今天天气怎么样？"
    print(f"\n👤 用户: {query}")
    answer = run_agent(query, verbose=True)
    print(f"✅ 最终回答: {answer}")


def demo3_multi_turn():
    """演示③：多轮工具调用 — 先查天气 → 再判断是否需要带伞"""
    print("\n" + "=" * 60)
    print("☔ 演示③：多轮推理 — 查天气 → 分析 → 给出建议")
    print("=" * 60)

    query = "我明天要去深圳出差，帮我查一下深圳的天气，然后告诉我需不需要带伞？"
    print(f"\n👤 用户: {query}")
    answer = run_agent(query, verbose=True)
    print(f"✅ 最终回答: {answer}")


# ╔══════════════════════════════════════════════════════════════╗
# ║  主入口                                                      ║
# ╚══════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 模块 3 Step 0 — Tool Use 热身运行")
    print(f"   模型: {MODEL}")
    print("=" * 60)

    demo1_calculator()
    demo2_weather()
    demo3_multi_turn()

    print("\n" + "=" * 60)
    print("🎉 三个演示运行完毕！")
    print("   观察要点：")
    print("   1. LLM 怎么知道该调用哪个工具？（看 tool_calls 里的 name）")
    print("   2. LLM 怎么传递参数？（看 tool_calls 里的 arguments）")
    print("   3. 工具执行结果怎么返回给 LLM？（看 tool 消息）")
    print("   4. 多轮调用时，对话历史怎么传递？")
    print("=" * 60)
