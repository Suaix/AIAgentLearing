"""
模块 3：Tool Use / Function Calling — Step 3 引导式修改
=========================================================

四个渐进式任务，通过命令行参数选择：
  uv run python code/03-tool-use/tool_definition_step3.py 1    # 任务① 改参数
  uv run python code/03-tool-use/tool_definition_step3.py 2    # 任务② 加功能
  uv run python code/03-tool-use/tool_definition_step3.py 3    # 任务③ 修 bug
  uv run python code/03-tool-use/tool_definition_step3.py 4    # 任务④ 扩展场景

基础架构来自 Step 0 热身代码，你需要完成各任务中的 TODO 部分。
"""

import os
import json
import sys
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
MODEL = "deepseek-v4-flash"


# ╔══════════════════════════════════════════════════════════════╗
# ║  共用基础：工具定义 + 执行器 + Agent Loop                     ║
# ╚══════════════════════════════════════════════════════════════╝

# ---- 工具 1：计算器 ----
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
                "a": {"type": "number", "description": "第一个操作数"},
                "b": {"type": "number", "description": "第二个操作数"},
            },
            "required": ["operation", "a", "b"],
        },
    },
}

# ---- 工具 2：天气查询（模拟） ----
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的实时天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如 Beijing, Shanghai",
                },
            },
            "required": ["city"],
        },
    },
}


# ---- 工具执行器 ----
def execute_calculator(operation: str, a: float, b: float) -> dict:
    if operation == "add":
        return {"result": a + b}
    elif operation == "subtract":
        return {"result": a - b}
    elif operation == "multiply":
        return {"result": a * b}
    elif operation == "divide":
        if b == 0:
            return {"error": "除数不能为零"}
        return {"result": a / b}
    return {"error": f"未知运算: {operation}"}


def execute_get_weather(city: str) -> dict:
    weather_db = {
        "beijing": {"temperature": 28, "humidity": 65, "condition": "晴天"},
        "shanghai": {"temperature": 32, "humidity": 80, "condition": "多云转阵雨"},
        "tokyo": {"temperature": 25, "humidity": 70, "condition": "小雨"},
        "shenzhen": {"temperature": 33, "humidity": 85, "condition": "雷阵雨"},
    }
    city_lower = city.lower()
    if city_lower in weather_db:
        return {"city": city, **weather_db[city_lower]}
    return {"city": city, "error": f"暂无 '{city}' 的天气数据"}


def execute_tool(tool_name: str, arguments: dict) -> str:
    if tool_name == "calculator":
        result = execute_calculator(**arguments)
    elif tool_name == "get_weather":
        result = execute_get_weather(**arguments)
    elif tool_name == "get_current_time":
        result = execute_get_current_time(**arguments)
    else:
        result = {"error": f"未知工具: {tool_name}"}
    return json.dumps(result, ensure_ascii=False)


def run_agent(
    user_query: str, tools: list, temperature: float = 0.1, verbose: bool = True
) -> str:
    """通用 Agent 循环：发送消息 → 执行工具 → 循环直到 LLM 返回纯文本"""
    messages = [{"role": "user", "content": user_query}]

    for turn in range(5):
        if verbose:
            print(f"\n--- 第 {turn + 1} 轮 ---")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            temperature=temperature,
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            print(f"  🔧 LLM 调用 {len(msg.tool_calls)} 个工具")
            messages.append(msg.model_dump())

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                arguments = json.loads(tc.function.arguments)
                result = execute_tool_v2(tool_name, arguments)
                print(
                    f"     {tool_name}({json.dumps(arguments, ensure_ascii=False)}) → {result}"
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )
            continue

        # 纯文本回答 → 结束
        if verbose:
            print(f"  💬 {msg.content}")
        return msg.content

    return "⚠️ 达到最大轮次"


# ╔══════════════════════════════════════════════════════════════╗
# ║  任务①：改参数 — 观察 temperature 对工具选择的影响          ║
# ╚══════════════════════════════════════════════════════════════╝
#
# 目标：理解 temperature 参数不仅影响文本生成，也影响工具选择的确定性。
#
# 运行：uv run python code/03-tool-use/tool_definition_step3.py 1
#
# 问题背景：
#   用户说 "帮我算一下 100+200"，意图非常明确——应该用 calculator 工具。
#   但如果用户说 "我想知道 100+200 是多少，对了今天北京热不热？"
#   这个请求既可以用 calculator 又可以用 get_weather。
#   当 temperature 较低时，模型倾向于选择"最可能"的工具；
#   当 temperature 较高时，模型可能做出不同的选择。
#
# 你的任务：
#   ① 补全下方的 queries 列表（至少 3 个"模糊意图"的查询）
#   ② 对每个查询分别用 temperature=0.0 和 temperature=1.5 运行
#   ③ 观察并记录：temperature 是否影响了工具选择？


def task1_temperature_effect():
    """任务①：对比不同 temperature 下的工具选择行为"""
    print("=" * 60)
    print("🔬 任务①：Temperature 对工具选择的影响")
    print("=" * 60)

    tools = [calculator_tool, weather_tool]

    # TODO: 设计 3 个"模糊意图"的查询 — 既可能用计算器也可能查天气
    # 提示：让查询同时涉及计算和天气，看 LLM 在不同 temperature 下如何选择
    queries = [
        # TODO: 你的第 1 个模糊查询
        "我想知道34*3等于多少，另外，我今天去北京看下需要带伞不？",
        # TODO: 你的第 2 个模糊查询
        "7号北京高考，天气还挺热的，数据考试中有一项5的2次方是多少？帮我算下",
        # TODO: 你的第 3 个模糊查询
        "帮我查下北京的温度和上海的温度差多少？",
    ]

    for query in queries:
        print(f"\n{'─'*40}")
        print(f"👤 用户: {query}")

        for temp in [0.0, 1.5]:
            print(f"\n  🌡️ temperature={temp}:")
            # TODO: 调用 run_agent() 并观察输出中的 "🔧 LLM 调用 X 个工具" 部分
            # 格式：run_agent(query, tools, temperature=temp)
            run_agent(query, tools, temperature=temp)

    print("\n💡 思考：temperature 高低分别适合什么场景？")


# ╔══════════════════════════════════════════════════════════════╗
# ║  任务②：加功能 — 添加一个新工具（获取当前时间）             ║
# ╚══════════════════════════════════════════════════════════════╝
#
# 目标：学会定义一个完整的新工具（Schema + 执行函数 + 注册）。
#
# 运行：uv run python code/03-tool-use/tool_definition_step3.py 2
#
# 你的任务：
#   ① 参考 calculator_tool 的格式，定义一个 get_current_time 工具
#      - name: "get_current_time"
#      - description: "获取当前日期和时间"
#      - parameters: 需要一个 "timezone" 参数（string 类型，默认 "Asia/Shanghai"）
#   ② 实现 execute_get_current_time 函数（用 Python 的 datetime 模块）
#   ③ 在 execute_tool 函数中注册这个新工具
#   ④ 运行测试：问 LLM "现在几点了？"


def execute_get_current_time(timezone: str = "Asia/Shanghai") -> dict:
    """返回当前日期时间"""
    now_time = datetime.now(ZoneInfo(timezone))
    return {"datetime": now_time.strftime("%Y-%m-%d %H:%M:%S"), "timezone": timezone}


def task2_add_tool():
    """任务②：添加 get_current_time 工具"""
    print("=" * 60)
    print("🔧 任务②：添加新工具 — get_current_time")
    print("=" * 60)

    # TODO ①: 定义 get_current_time_tool（参考上面 calculator_tool 的格式）
    get_current_time_tool = {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期和时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "获取日期和时间的时区",
                    },
                },
                "required": ["timezone"],
            },
        },
    }
    tools = [calculator_tool, weather_tool, get_current_time_tool]
    query = "现在几点了？"
    answer = run_agent(query, tools)
    print(f"\n结果: {answer}")

    print("\n⚠️ 请完成上述 TODO 后运行测试。")

    # 提示：因为 execute_tool 在文件顶部定义，你需要在这里重新定义或修改顶部的函数。
    # 建议做法：在当前函数内实现"新版本"的 execute_tool 和 run_agent，
    # 或者直接修改文件顶部的 execute_tool 函数。


# ╔══════════════════════════════════════════════════════════════╗
# ║  任务③：修 Bug — 工具调用中的异常处理                       ║
# ╚══════════════════════════════════════════════════════════════╝
#
# 目标：理解 Tool Use 中常见的出错场景及其处理方式。
#
# 运行：uv run python code/03-tool-use/tool_definition_step3.py 3
#
# 背景：
#   下面的 task3_buggy_code() 包含 2 个故意埋入的 bug。
#   bug1 会导致 LLM 调用工具失败（参数验证问题）
#   bug2 会导致工具执行成功但结果无法正确返回给 LLM（消息格式问题）
#
# 你的任务：
#   ① 运行代码，观察错误现象
#   ② 定位 bug 的根因
#   ③ 修复两个 bug，使代码正常运行
#
# 提示：
#   - 仔细看 execute_calculator 的参数签名和 tool definition 里的 required 字段
#   - 检查 tool 消息的格式是否正确


def task3_fix_bugs():
    """任务③：修复工具调用中的 bug"""
    print("=" * 60)
    print("🐛 任务③：修复 Bug")
    print("=" * 60)

    # ---- Bug 1 区域：工具定义和参数不匹配 ----
    # 下面这个计算器工具的 parameters.required 包含了 "operation", "a", "b"
    # 但 execute_buggy_calculator 的函数签名是 execute_buggy_calculator(op, x, y)
    # 参数名不匹配会导致 **arguments 解包失败！
    #
    # 你的任务：找出参数名不一致的地方，统一它们。

    buggy_calculator_tool = {
        "type": "function",
        "function": {
            "name": "buggy_calculator",
            "description": "计算两个数的结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "op": {  # ← 注意：这里的参数名
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                    },
                    "x": {"type": "number"},  # ← 注意：这里的参数名
                    "y": {"type": "number"},  # ← 注意：这里的参数名
                },
                "required": ["op", "x", "y"],
            },
        },
    }

    # BUG 1：下面这个函数的参数名和上面 JSON Schema 定义的参数名一致吗？
    # 提示：仔细对比 op/x/y vs operation/a/b
    def execute_buggy_calculator(op: str, x: float, y: float) -> dict:
        if op == "add":
            return {"result": x + y}
        elif op == "subtract":
            return {"result": x - y}
        elif op == "multiply":
            return {"result": x * y}
        elif op == "divide":
            # BUG 2：缺少除零检查！
            if y == 0:
                return {"error": "除数不能为零"}
            return {"result": x / y}
        return {"error": f"未知运算: {op}"}

    # BUG 3：下方 execute_buggy_tool 里 tool 消息缺少 tool_call_id
    # 或者 tool_call_id 的值不对
    def execute_buggy_tool(tool_name: str, arguments: dict) -> str:
        if tool_name == "buggy_calculator":
            result = execute_buggy_calculator(**arguments)
        else:
            result = {"error": f"未知工具: {tool_name}"}
        return json.dumps(result, ensure_ascii=False)

    # ---- 测试 ----
    # TODO: 运行以下代码，观察报错信息，然后修复上面的 bug
    # 修复后，这个查询应该能正常返回结果

    print("\n运行 Buggy 代码测试...")
    messages = [{"role": "user", "content": "帮我算一下 50 除以 0 等于多少？"}]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[buggy_calculator_tool],
            temperature=0.1,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            print(f"  LLM 调用工具: {msg.tool_calls[0].function.name}")
            print(f"  参数: {msg.tool_calls[0].function.arguments}")

            tc = msg.tool_calls[0]
            arguments = json.loads(tc.function.arguments)
            result = execute_buggy_tool(tc.function.name, arguments)

            messages.append(msg.model_dump())

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

            # 第二轮：让 LLM 看到结果
            response2 = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
            )
            print(f"  最终回答: {response2.choices[0].message.content}")
        else:
            print(f"  直接回答（未调工具）: {msg.content}")
    except Exception as e:
        print(f"  ❌ 出错了！错误信息: {e}")
        print("\n  🔍 调试提示：")
        print(
            "  1. 检查 execute_buggy_calculator 的**参数名**是否和 JSON Schema 里的一致"
        )
        print("  2. 检查除零操作有没有被处理")
        print("  3. 检查 tool 消息里是否包含了 tool_call_id")

    print("\n💡 修复所有 bug 后重新运行，确认不再报错且 LLM 能正确处理 '50除以0'。")


# ╔══════════════════════════════════════════════════════════════╗
# ║  任务④：扩展场景 — 添加数据库查询工具，实现多工具组合       ║
# ╚══════════════════════════════════════════════════════════════╝
#
# 目标：添加一个模拟数据库查询工具，让 LLM 先查数据库再计算。
#
# 运行：uv run python code/03-tool-use/tool_definition_step3.py 4
#
# 场景：你有一个"产品库存数据库"（模拟），里面有产品名称、单价、库存量。
#      用户可能问："A 产品库存总价值是多少？"（需要查单价×库存）
#      或者 "B 产品打 8 折后多少钱？"（需要查单价×折扣）
#
# 你的任务：
#   ① 定义 query_product 工具（查询产品信息，Schema 需要 product_name 参数）
#   ② 实现 execute_query_product 函数（模拟数据库查询）
#   ③ 实现新的 execute_tool（支持 calculator + query_product）
#   ④ 设计 2 个测试查询，验证 LLM 能组合使用两个工具

# ---- 模拟数据库 ----
PRODUCT_DB = {
    "iphone16": {"name": "iPhone 16", "price": 6999, "stock": 150},
    "macbook_pro": {"name": "MacBook Pro 14", "price": 14999, "stock": 80},
    "airpods_pro": {"name": "AirPods Pro 2", "price": 1899, "stock": 300},
    "ipad_air": {"name": "iPad Air", "price": 4799, "stock": 120},
    "apple_watch": {"name": "Apple Watch S9", "price": 2999, "stock": 200},
}


# TODO ②: 实现执行函数
def execute_query_product(product_name: str) -> dict:
    """从 PRODUCT_DB 中查询产品信息"""
    product = PRODUCT_DB.get(product_name.lower())
    if product:
        return product
    else:
        return {"error": f"未找到产品 '{product_name}'"}

    #     # 提示：用 product_name.lower() 在 PRODUCT_DB 中查找
    #     # 如果找到，返回产品信息字典
    #     # 如果没找到，返回 {"error": f"未找到产品 '{product_name}'"}
    #     pass  # 替换为你的实现

    # TODO ③: 实现新的 execute_tool（或修改顶部函数）


def execute_tool_v2(tool_name: str, arguments: dict) -> str:
    if tool_name == "calculator":
        result = execute_calculator(**arguments)
    elif tool_name == "query_product":
        result = execute_query_product(**arguments)
    else:
        result = {"error": "未知工具调用"}
    return json.dumps(result, ensure_ascii=False)


def task4_extend_scenario():
    """任务④：添加数据库查询工具 + 多工具组合"""
    print("=" * 60)
    print("🏗️ 任务④：扩展场景 — 产品库存查询 + 计算")
    print("=" * 60)

    # TODO ①: 定义 query_product 工具
    # 提示：工具名 = "query_product"
    #       description = "查询产品信息，返回产品名称、单价和库存量"
    #       parameters 需要 product_name（string, required）
    query_product_tool = {
        "type": "function",
        "function": {
            "name": "query_product",
            "description": "查询商品信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "商品名称",
                    },
                },
                "required": ["product_name"],
            },
        },
    }

    # TODO ④: 设计测试查询并运行
    tools = [calculator_tool, query_product_tool]
    #
    # 测试查询示例：
    #   1. "iPhone 16 的库存总价值是多少？"（需要查单价×库存）
    #   2. "如果 MacBook Pro 打 8 折，新价格是多少？"（需要查单价×0.8）
    #   3. 你自己再设计一个需要组合两个工具的查询
    #
    queries = [
        "iPhone 16 的库存总价值是多少？(需要查单价×库存)",
        "如果 MacBook Pro 打 8 折，新价格是多少？（需要查单价×0.8）",
        "帮我查一下ipad_air现在单价多少，如果我要买10台需要多少钱？",
    ]
    for q in queries:
        print(f"\n👤 {q}")
        answer = run_agent(q, tools)
        print(f"✅ {answer}")

    print("\n⚠️ 请完成上述 TODO 后运行测试。")
    print("   提示：修改顶部的 execute_tool 函数，或在本函数内实现 v2 版本。")


# ╔══════════════════════════════════════════════════════════════╗
# ║  主入口：通过命令行参数分发任务                               ║
# ╚══════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "用法: uv run python code/03-tool-use/tool_definition_step3.py <任务编号>"
        )
        print("  1 — 改参数：观察 temperature 对工具选择的影响")
        print("  2 — 加功能：添加 get_current_time 工具")
        print("  3 — 修 Bug：修复工具调用中的异常")
        print("  4 — 扩展场景：数据库查询 + 计算器组合")
        sys.exit(1)

    task_num = sys.argv[1]

    if task_num == "1":
        task1_temperature_effect()
    elif task_num == "2":
        task2_add_tool()
    elif task_num == "3":
        task3_fix_bugs()
    elif task_num == "4":
        task4_extend_scenario()
    else:
        print(f"❌ 未知任务编号: {task_num}，请输入 1-4")
        sys.exit(1)
