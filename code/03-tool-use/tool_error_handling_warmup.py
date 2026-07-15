"""
Step 0 热身运行 — Tool Use 错误处理、超时与重试策略

运行方式：
    uv run python code/03-tool-use/tool_error_handling_warmup.py

本文件演示三种典型错误场景：
    场景1 — 工具执行超时（模拟网络请求过慢）
    场景2 — 工具返回错误（API 返回异常数据）
    场景3 — 工具参数格式错误（LLM 传了错误类型的参数）

每个场景展示 Agent 的"观察-重试"循环。
"""

import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── 客户端初始化（使用 DeepSeek API，兼容 OpenAI SDK）───────
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
MODEL = "deepseek-v4-flash"


# ═══════════════════════════════════════════════════════════════
# 工具定义
# ═══════════════════════════════════════════════════════════════

# ── 工具1：模拟一个"可能超时"的搜索引擎 ──
def web_search(query: str, timeout: float = 1.0) -> dict:
    """模拟网络搜索（可能超时）。"""
    # 模拟：查询太短时"网络很慢"（触发超时）
    if len(query) < 3:
        time.sleep(3.0)  # 模拟超时
        return {"error": "timeout", "message": f"搜索超时: query='{query}'"}
    # 正常返回
    return {
        "status": "ok",
        "query": query,
        "results": [
            {"title": f"关于 '{query}' 的结果1", "snippet": "..."},
            {"title": f"关于 '{query}' 的结果2", "snippet": "..."},
        ],
    }


# ── 工具2：模拟一个"可能返回错误"的数据库查询 ──
def db_query(sql: str) -> dict:
    """模拟数据库查询（可能返回错误）。"""
    # 模拟：某些 SQL 会失败
    forbidden_keywords = ["DROP", "DELETE", "ALTER"]
    for kw in forbidden_keywords:
        if kw in sql.upper():
            return {"error": "permission_denied", "message": f"禁止执行 {kw} 操作"}
    # 模拟：语法错误
    if "FROM" not in sql.upper():
        return {"error": "syntax_error", "message": f"SQL 语法错误: 缺少 FROM 子句"}
    # 正常返回
    return {
        "status": "ok",
        "sql": sql,
        "rows": [{"id": 1, "name": "示例数据"}],
        "count": 1,
    }


# ── 工具3：模拟一个"对参数格式敏感"的数学计算器 ──
def calculator(expression: str) -> dict:
    """安全的数学表达式计算器。"""
    try:
        # 安全评估（仅允许数字和基本运算符）
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return {"error": "invalid_chars", "message": f"表达式包含非法字符: '{expression}'"}
        result = eval(expression)  # 安全：已过滤字符
        return {"status": "ok", "expression": expression, "result": result}
    except ZeroDivisionError:
        return {"error": "division_by_zero", "message": "除数不能为0"}
    except SyntaxError:
        return {"error": "syntax_error", "message": f"表达式语法错误: '{expression}'"}
    except Exception as e:
        return {"error": "unknown", "message": str(e)}


# ── 工具4：正常天气查询（作为"可靠工具"的参照）──
def get_weather(city: str) -> dict:
    """查询城市天气（可靠的正常工具）。"""
    weather_data = {
        "北京": {"temp": 32, "condition": "晴", "humidity": "45%"},
        "上海": {"temp": 28, "condition": "多云", "humidity": "70%"},
        "深圳": {"temp": 33, "condition": "雷阵雨", "humidity": "85%"},
    }
    info = weather_data.get(city, {"temp": 25, "condition": "未知", "humidity": "50%"})
    return {"status": "ok", "city": city, **info}


# ═══════════════════════════════════════════════════════════════
# 工具 Schema 定义（OpenAI 格式）
# ═══════════════════════════════════════════════════════════════

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网获取信息。注意：查询词太短可能导致超时。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词，建议至少5个字符"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "db_query",
            "description": "执行SQL查询。注意：不支持 DROP/DELETE/ALTER 操作，SQL必须包含FROM子句。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL查询语句（仅SELECT）"},
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式。仅支持数字和 + - * / ( ) . % 运算符。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 '(3+5)*2'"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如'北京'"},
                },
                "required": ["city"],
            },
        },
    },
]

# 工具名 → 函数映射
TOOL_MAP: dict[str, Any] = {
    "web_search": web_search,
    "db_query": db_query,
    "calculator": calculator,
    "get_weather": get_weather,
}


# ═══════════════════════════════════════════════════════════════
# Agent 循环（带错误计数和最大重试）
# ═══════════════════════════════════════════════════════════════

def run_agent(user_message: str, max_turns: int = 6, verbose: bool = True) -> list[dict]:
    """
    带错误感知的 Agent 循环。

    与之前 warmup 的关键区别：
    - 每轮检查工具是否返回 error，如果是则反馈给 LLM 让其重试
    - 记录错误计数
    - max_turns 防止无限重试
    """
    messages: list[dict] = [
        {"role": "system", "content": (
            "你是一个有帮助的助手，可以调用工具来完成任务。\n"
            "重要规则：\n"
            "1. 如果工具返回了 error，仔细阅读 error message，调整参数后重试\n"
            "2. 同一工具连续失败2次后，尝试换一种方式或告诉用户你遇到了问题\n"
            "3. 工具调用超时时，尝试缩短查询词或用更简单的参数重试"
        )},
        {"role": "user", "content": user_message},
    ]

    tool_call_history: list[dict] = []

    for turn in range(1, max_turns + 1):
        # ── 调用 LLM ──
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        assistant_msg = response.choices[0].message

        # ── 无 tool_calls → 纯文本回答，Agent 循环结束 ──
        if not assistant_msg.tool_calls:
            if verbose:
                print(f"\n{'='*60}")
                print(f"✅ [第{turn}轮] Agent 最终回答（无工具调用）:")
                print(f"{'='*60}")
                print(assistant_msg.content)
            messages.append({"role": "assistant", "content": assistant_msg.content})
            break

        # ── 执行工具调用 ──
        messages.append({
            "role": "assistant",
            "content": assistant_msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in assistant_msg.tool_calls
            ],
        })

        for tc in assistant_msg.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)

            if verbose:
                print(f"\n{'─'*50}")
                print(f"🔧 [第{turn}轮] 调用工具: {func_name}({json.dumps(args, ensure_ascii=False)})")

            # 执行工具函数
            func = TOOL_MAP.get(func_name)
            if func is None:
                result = {"error": "unknown_tool", "message": f"未知工具: {func_name}"}
            else:
                result = func(**args)

            if verbose:
                result_str = json.dumps(result, ensure_ascii=False)
                # 如果是错误，高亮显示
                if "error" in result:
                    print(f"   ⚠️  工具返回错误: {result_str}")
                else:
                    print(f"   ✅ 工具返回: {result_str[:120]}{'...' if len(result_str) > 120 else ''}")

            tool_call_history.append({
                "turn": turn,
                "tool": func_name,
                "args": args,
                "result": result,
                "is_error": "error" in result,
            })

            # 将工具结果反馈给 LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    if verbose and turn >= max_turns:
        print(f"\n⚠️  达到最大轮次限制 ({max_turns})，Agent 被迫停止。")

    return tool_call_history


# ═══════════════════════════════════════════════════════════════
# 三个演示场景
# ═══════════════════════════════════════════════════════════════

def scene1_timeout_and_retry():
    """场景1：工具执行超时 → Agent 自行调整重试"""
    print("\n" + "█" * 60)
    print("场景1：搜索引擎超时 → Agent 重试（调整查询参数）")
    print("█" * 60)
    print("\n用户要求：「帮我搜一下 AI」")
    print("→ 查询词只有2个字，web_search 会触发超时模拟")
    print("→ 期望：Agent 看到超时错误后，自动用更长的查询词重试\n")

    history = run_agent("帮我搜一下 AI")
    return history


def scene2_tool_returns_error():
    """场景2：工具返回错误 → Agent 换方式重试"""
    print("\n" + "█" * 60)
    print("场景2：数据库查询被拒绝 → Agent 换方法重试")
    print("█" * 60)
    print("\n用户要求：「帮我把users表里所有数据删掉」")
    print("→ DELETE 被 db_query 拒绝（权限不足）")
    print("→ 期望：Agent 看到错误后，向用户解释并建议替代方案\n")

    history = run_agent("帮我把users表里所有数据删掉")
    return history


def scene3_bad_params_and_retry():
    """场景3：工具参数错误 → Agent 修正参数重试"""
    print("\n" + "█" * 60)
    print("场景3：计算器参数错误 → Agent 修正后重试")
    print("█" * 60)
    print("\n用户要求：「帮我算一下 sum(1,2,3)」")
    print("→ LLM 可能传 'sum(1,2,3)' 给 calculator，calculator 只接受纯数学表达式")
    print("→ 期望：Agent 看到错误后，将 sum 转为 '(1+2+3)' 重试\n")

    history = run_agent("帮我算一下 sum(1,2,3)")
    return history


# ═══════════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("模块3 子主题4 — 错误处理、超时与重试策略")
    print("Step 0 热身运行")
    print("=" * 60)

    scene1_timeout_and_retry()
    scene2_tool_returns_error()
    scene3_bad_params_and_retry()

    print("\n" + "=" * 60)
    print("🎉 三个场景运行完毕！")
    print("请观察每个场景中 Agent 如何应对工具返回的错误。")
    print("=" * 60)
