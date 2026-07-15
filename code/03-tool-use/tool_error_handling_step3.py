"""
Step 3 引导式修改 — Tool Use 错误处理、超时与重试策略
======================================================

运行方式：
    uv run python code/03-tool-use/tool_error_handling_step3.py 1    # 任务①
    uv run python code/03-tool-use/tool_error_handling_step3.py 2    # 任务②
    uv run python code/03-tool-use/tool_error_handling_step3.py 3    # 任务③
    uv run python code/03-tool-use/tool_error_handling_step3.py 4    # 任务④

四个任务：
    ① 改参数 — 超时阈值 & 重试次数实验
    ② 加功能 — 实现真实的超时包装器 call_with_timeout
    ③ 修 bug  — 重试计数器未按工具名区分
    ④ 新场景 — 实现多级降级链（主源→备源→缓存→用户通知）
"""

import json
import os
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Callable
from unittest import result

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# 配置区
# ═══════════════════════════════════════════════════════════════

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
MODEL = "deepseek-v4-flash"

# ── 超时与重试配置（任务①会修改这里的值做实验）──
RETRY_CONFIG = {
    "tool_timeout": 2.0,  # 单个工具调用的超时时间（秒）
    "max_retries": 3,  # 同一工具最大重试次数
    "max_turns": 8,  # Agent 循环最大轮数
}

# ── 天气缓存 & 降级演示开关（任务④会用到）──
WEATHER_CACHE: dict[str, dict] = {
    "北京": {"temp": 30, "condition": "晴", "source": "cache"},
    "上海": {"temp": 27, "condition": "多云", "source": "cache"},
}
_FORCE_FAIL_DEMO = False  # 任务④强制降级演示开关


# ═══════════════════════════════════════════════════════════════
# 模拟工具函数（三种不同的"不可靠"程度）
# ═══════════════════════════════════════════════════════════════


def get_weather_primary(city: str) -> dict:
    """
    主天气数据源（模拟：30% 概率连接失败）。
    不可预判错误 —— LLM 不知道这次调用会不会失败。
    """
    if _FORCE_FAIL_DEMO or random.random() < 0.3:
        time.sleep(0.2)  # 短暂延迟模拟网络开销
        return {"error": "connection_failed", "message": f"主数据源连接失败: {city}"}
    return {
        "status": "ok",
        "city": city,
        "temp": random.randint(20, 35),
        "condition": random.choice(["晴", "多云", "小雨"]),
        "source": "primary",
    }


def get_weather_fallback(city: str) -> dict:
    """
    备用天气数据源（模拟：更可靠但数据不够详细）。
    10% 概率失败。
    """
    if _FORCE_FAIL_DEMO or random.random() < 0.1:
        return {"error": "service_unavailable", "message": "备用数据源暂时不可用"}
    return {
        "status": "ok",
        "city": city,
        "temp": random.randint(20, 35),
        "source": "fallback",
    }


def web_search(query: str) -> dict:
    """
    模拟搜索引擎（不可预判错误：30% 概率触发慢查询导致超时）。

    与 warmup 的关键区别：
    - warmup 用 query 长度判断（可预判，LLM 能规避）
    - 这里用随机概率（不可预判，LLM 无法规避）——这才是超时机制真正要应对的场景
    """
    if random.random() < 0.3:
        time.sleep(3.0)  # 模拟网络抖动，30% 概率慢查询
        return {"error": "timeout", "message": "搜索请求超时，请重试或缩短查询范围"}
    return {
        "status": "ok",
        "query": query,
        "results": [{"title": f"搜索结果: {query}", "snippet": "..."}],
    }


def calculator(expression: str) -> dict:
    """安全的数学计算器。"""
    try:
        allowed = set("0123456789+-*/().% ^")
        if not all(c in allowed for c in expression):
            return {"error": "invalid_chars", "message": f"非法字符: '{expression}'"}
        # 替换 ^ 为 ** 方便运算
        expr = expression.replace("^", "**")
        result = eval(expr)
        return {"status": "ok", "expression": expression, "result": result}
    except ZeroDivisionError:
        return {"error": "division_by_zero", "message": "除数不能为0"}
    except Exception as e:
        return {"error": "eval_error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════
# 任务② 需要的：真实超时包装器（TODO 待实现）
# ═══════════════════════════════════════════════════════════════


def call_with_timeout(func: Callable, kwargs: dict, timeout: float) -> dict:
    """
    用真实超时机制包装任意工具函数。

    要求：
    - 在独立线程中执行 func(**kwargs)
    - 如果在 timeout 秒内完成，返回执行结果
    - 如果超时，返回 {"error": "timeout", "message": "..."}
    - 如果 func 本身抛异常，捕获并返回 {"error": "exception", "message": "..."}

    提示：使用 concurrent.futures.ThreadPoolExecutor(max_workers=1)
          然后用 future.result(timeout=...) 等待结果
          捕获 concurrent.futures.TimeoutError 来处理超时
    """
    # TODO: 你的代码 — 实现真实超时包装器
    # 1. 创建 ThreadPoolExecutor(max_workers=1)
    # 2. 提交 func(**kwargs) 到 executor
    # 3. 调用 future.result(timeout=timeout) 获取结果
    # 4. 超时捕获、异常捕获 → 返回对应的 error dict
    # 5. finally 中关闭 executor
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func, **kwargs)
    try:
        result = future.result(timeout=timeout)
        return result
    except TimeoutError as err:
        return {"error": "timeout", "message": str(err)}
    except Exception as e:
        return {"error": "exception", "message": str(e)}
    finally:
        executor.shutdown()


# ═══════════════════════════════════════════════════════════════
# 任务④ 需要的：多级降级链（TODO 待实现）
# ═══════════════════════════════════════════════════════════════


def get_weather_with_fallback(city: str) -> dict:
    """
    多级降级查询天气：主源 → 备用源 → 缓存 → 失败通知。

    降级链：
        Level 1: 调用 get_weather_primary(city)
                 → 成功则返回，失败则进入 Level 2
        Level 2: 调用 get_weather_fallback(city)
                 → 成功则返回，失败则进入 Level 3
        Level 3: 查 WEATHER_CACHE[city]
                 → 命中则返回（标注 source="cache"），未命中进入 Level 4
        Level 4: 返回 error，告知用户所有数据源均不可用

    返回格式：与 get_weather_primary 一致（包含 source 字段标明数据来源）
    """
    # TODO: 你的代码 — 实现四级降级链
    # 提示：
    #   result = get_weather_primary(city)
    #   if "error" not in result: return result
    #   result = get_weather_fallback(city)
    #   if "error" not in result: return result
    #   if city in WEATHER_CACHE: return WEATHER_CACHE[city]
    #   return {"error": "all_sources_failed", ...}
    result = get_weather_primary(city)
    if "error" not in result:
        return result

    result = get_weather_fallback(city)
    if "error" not in result:
        return result

    if city in WEATHER_CACHE:
        return WEATHER_CACHE[city]

    return {
        "error": "all_sources_faild",
        "message": "failed to get weather, all sources are failed.",
    }


# ═══════════════════════════════════════════════════════════════
# Tool Schema 定义
# ═══════════════════════════════════════════════════════════════

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询城市天气（含降级链：主源→备源→缓存）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网获取信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式。支持 + - * / ( ) % ^。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"},
                },
                "required": ["expression"],
            },
        },
    },
]

# 工具名 → 函数映射
TOOL_MAP: dict[str, Any] = {
    "get_weather": get_weather_with_fallback,  # 任务④启用降级链后生效
    "web_search": web_search,
    "calculator": calculator,
}


# ═══════════════════════════════════════════════════════════════
# Agent 循环（含错误计数和重试控制）
# ═══════════════════════════════════════════════════════════════


def run_agent(user_message: str, config: dict | None = None) -> list[dict]:
    """
    带错误处理和重试控制的 Agent 循环。

    与 warmup 的关键区别：
    - 记录每个工具的连续失败次数（任务③需要修复的 bug 就在这一块）
    - 支持真实的超时中断
    - 支持降级反馈
    """
    cfg = config or RETRY_CONFIG
    timeout = cfg["tool_timeout"]
    max_turns = cfg["max_turns"]

    messages: list[dict] = [
        {
            "role": "system",
            "content": (
                "你是一个有帮助的助手，可以调用工具来完成任务。\n"
                "错误处理规则：\n"
                "1. 如果工具返回 error，仔细阅读 error message，调整参数后重试\n"
                "2. 同一工具连续失败2次后，告诉用户遇到了什么问题，不要继续重试\n"
                "3. 如果错误信息显式建议了替代方案，优先尝试替代方案"
            ),
        },
        {"role": "user", "content": user_message},
    ]

    history: list[dict] = []

    # ⚠️ BUG 在这里（任务③）：consecutive_errors 没有按工具名区分
    # 修改前：所有工具共用一个失败计数器
    # 修改后：应该用 dict[str, int] 按工具名分别计数
    # consecutive_errors = 0  # ← 任务③：改成 dict[str, int]
    consecutive_errors: dict[str, int] = {}

    for turn in range(1, max_turns + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        assistant_msg = response.choices[0].message

        if not assistant_msg.tool_calls:
            print(f"\n✅ [第{turn}轮] Agent 结束:")
            print(f"   {assistant_msg.content}")
            messages.append({"role": "assistant", "content": assistant_msg.content})
            break

        messages.append(
            {
                "role": "assistant",
                "content": assistant_msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_msg.tool_calls
                ],
            }
        )

        for tc in assistant_msg.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)

            print(
                f"\n🔧 [第{turn}轮] {func_name}({json.dumps(args, ensure_ascii=False)})"
            )

            func = TOOL_MAP.get(func_name)
            if func is None:
                result = {"error": "unknown_tool", "message": f"未知工具: {func_name}"}
            else:
                # ── 超时包装调用（任务②完成后 timeout 才会实际生效）──
                result = call_with_timeout(func, args, timeout)
                # 注意：call_with_timeout 目前是 pass（返回 None），
                # 完成任务②的实现后，超时保护才会真正工作。
                # 那时再回来跑任务①，修改 tool_timeout 就能看到差异了。

            if result:
                error_flag = "error" in result
            else:
                error_flag = ""

            # ── 任务③ 需要修改的失败计数逻辑 ──
            if error_flag:
                consecutive_errors[func_name] = consecutive_errors.get(func_name, 0) + 1
                print(
                    f"   ⚠️  错误 (连续{consecutive_errors[func_name]}次): {json.dumps(result, ensure_ascii=False)}"
                )
            else:
                consecutive_errors[func_name] = 0
                print(f"   ✅ {json.dumps(result, ensure_ascii=False)[:120]}")

            history.append(
                {
                    "turn": turn,
                    "tool": func_name,
                    "args": args,
                    "result": result,
                    "is_error": error_flag,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return history


# ═══════════════════════════════════════════════════════════════
# 任务①：改参数 — max_turns 截断实验
# ═══════════════════════════════════════════════════════════════


def task1():
    """修改 max_turns，观察 Agent 循环被截断时的行为。"""
    print("=" * 60)
    print("任务①：max_turns 截断实验")
    print("=" * 60)
    print()
    print("提示：task② 已完成，现在 tool_timeout 已通过 call_with_timeout 生效。")
    print("      web_search 有 30% 概率触发 3 秒慢查询（不可预判错误）。")
    print("      tool_timeout=0.5s → 遇到慢查询时 call_with_timeout 会在 0.5s 后掐断。")
    print()

    # ── 实验：修改下面两个参数，每次跑 2-3 遍观察差异 ──
    # tool_timeout=0.5  → 慢查询大概率被掐断，Agent 看到 timeout error
    # tool_timeout=5.0  → 慢查询能跑完（3秒），Agent 正常拿到结果
    # max_turns=2       → Agent 可能来不及重试就被截断
    # max_turns=8       → Agent 有充足轮数处理错误和重试

    custom_config = {
        "tool_timeout": 0.5,  # TODO: 分别试 0.5 和 5.0
        "max_retries": 3,  # TODO: 修改这个值做实验
        "max_turns": 8,  # TODO: 分别试 2 和 8
    }

    print(
        f"当前配置: timeout={custom_config['tool_timeout']}s, "
        f"max_retries={custom_config['max_retries']}, max_turns={custom_config['max_turns']}"
    )
    print()

    # 这个用户请求需要搜索 + 查天气，至少2轮工具调用
    run_agent(
        "北京今天天气怎么样？另外帮我搜一下'AI Agent 错误处理最佳实践的最新进展'",
        config=custom_config,
    )

    print("\n" + "─" * 50)
    print("💡 对比实验（建议每改一次参数跑 2-3 遍，因为 web_search 是随机慢查询）：")
    print("  1. tool_timeout=0.5 → 大概率看到 '调用工具超时' 的 error")
    print("  2. tool_timeout=5.0 → 慢查询能跑完，Agent 正常响应")
    print("  3. max_turns=2  + 工具连续失败 → Agent 被迫截断，体验差")
    print("  4. 这说明：timeout 是'可预判错误'和'不可预判错误'之间的分界线")


# ═══════════════════════════════════════════════════════════════
# 任务②：加功能 — 实现真实超时包装器
# ═══════════════════════════════════════════════════════════════


def task2():
    """实现 call_with_timeout，然后跑测试验证。"""
    print("=" * 60)
    print("任务②：实现真实的超时包装器 call_with_timeout")
    print("=" * 60)
    print()

    # 步骤1：先实现上面第 102~125 行的 call_with_timeout 函数
    # 步骤2：运行本任务验证你的实现

    print("── 测试1：正常完成的函数 ──")

    # TODO 完成后，取消下面测试代码的注释
    print("  请在完成 call_with_timeout 实现后取消测试代码注释")

    def fast_func(x, y):
        return {"sum": x + y}

    #
    result = call_with_timeout(fast_func, {"x": 3, "y": 5}, timeout=2.0)
    print(f"   预期: {{'sum': 8}}")
    print(f"   实际: {result}")
    assert result == {"sum": 8}, f"测试1失败: {result}"

    print()
    print("── 测试2：超时的函数 ──")
    print("  请在完成 call_with_timeout 实现后取消测试代码注释")

    def slow_func():
        time.sleep(3.0)
        return {"done": True}

    result = call_with_timeout(slow_func, {}, timeout=1.0)
    print(f"   预期: {{'error': 'timeout', ...}}")
    print(f"   实际: {result}")
    assert "error" in result and result["error"] == "timeout", f"测试2失败: {result}"

    print()
    print("── 测试3：抛出异常的函数 ──")
    print("  请在完成 call_with_timeout 实现后取消测试代码注释")

    def buggy_func():
        raise ValueError("something went wrong")

    result = call_with_timeout(buggy_func, {}, timeout=2.0)
    print(f"   预期: {{'error': 'exception', ...}}")
    print(f"   实际: {result}")
    assert "error" in result and result["error"] == "exception", f"测试3失败: {result}"

    print()
    print("── 步骤3：集成到 Agent 循环 ──")
    print("  取消 run_agent 中第 243 行附近的两行注释:")
    print("    # result = func(**args)           ← 注释掉这行")
    print("    # result = call_with_timeout(...) ← 取消这行注释")
    run_agent(
        "帮我搜索下以下内容：当前AI发展日新月异，但作为普通人却无法介入进去，感觉到慌慌的，请问下我该如何调整才能参与到AI的发展历程里",
        {"tool_timeout": 0.5, "max_turns": 3},
    )
    print("  然后运行: uv run python code/03-tool-use/tool_error_handling_step3.py 2")
    print("  观察搜索长查询时，Agent 是否收到真实的 timeout 错误")


# ═══════════════════════════════════════════════════════════════
# 任务③：修 bug — 重试计数器按工具名区分
# ═══════════════════════════════════════════════════════════════


def task3():
    """修复 Bug：重试计数器应区分不同工具。"""
    print("=" * 60)
    print("任务③：修复 Bug — 重试计数器不区分工具名")
    print("=" * 60)
    print()

    print("── Bug 说明 ──")
    print("当前 run_agent 中（约第 230 行）：")
    print("  consecutive_errors = 0          # ← 所有工具共用一个计数器")
    print("  ...")
    print("  if error_flag:")
    print("      consecutive_errors += 1     # ← 不区分是哪个工具报的错")
    print()
    print("问题场景：")
    print("  1. calculator 报错1次 → consecutive_errors = 1")
    print(
        "  2. 下一轮 Agent 换用 web_search，web_search 也报错 → consecutive_errors = 2"
    )
    print("  3. System Prompt 看到'同一工具连续失败2次'→ 可能错误地放弃 web_search")
    print("  但实际上 web_search 才失败了1次！")
    print()

    # ── 用特定场景触发 Bug ──
    print("── 触发 Bug 的测试 ──")
    print("请求：'帮我算一下 100/0，然后搜一下 AI'")
    print("预期 Bug 表现：calculator 报错(除零)后，如果 web_search 也失败")
    print("              Agent 可能认为'同一工具'连续失败，过早放弃")
    print()

    # TODO: 你的修复
    # 1. 找到 run_agent 中的 consecutive_errors = 0
    # 2. 改为 per_tool_errors: dict[str, int] = {}
    # 3. 在错误处理逻辑中按 func_name 分别计数
    # 4. System Prompt 的"连续失败2次"判断应基于当前工具名查 per_tool_errors
    #
    # 修改完成后运行此任务验证：
    #   uv run python code/03-tool-use/tool_error_handling_step3.py 3

    run_agent("帮我算一下 100/0，然后搜一下 AI")

    print()
    print("── 修复后的预期行为 ──")
    print("  calculator 报错 → per_tool_errors['calculator'] = 1")
    print("  web_search 报错 → per_tool_errors['web_search'] = 1")
    print("  两个工具各自计数，不会互相干扰")


# ═══════════════════════════════════════════════════════════════
# 任务④：新场景 — 实现多级降级链
# ═══════════════════════════════════════════════════════════════


def task4():
    """实现并测试多级降级链：主源→备源→缓存→通知。"""
    print("=" * 60)
    print("任务④：实现多级降级链（Graceful Degradation）")
    print("=" * 60)
    print()

    print("── 需求说明 ──")
    print("get_weather_with_fallback(city) 需要实现四级降级：")
    print("  Level 1: get_weather_primary(city)    ← 主数据源（30% 可能失败）")
    print("  Level 2: get_weather_fallback(city)   ← 备用数据源（10% 可能失败）")
    print("  Level 3: WEATHER_CACHE[city]          ← 本地缓存")
    print("  Level 4: 返回 error 告知用户           ← 全部失败")
    print()
    print("关键设计点：")
    print("  - 每级返回都要标注 source 字段（primary/fallback/cache）")
    print("  - 缓存命中时要让用户知道数据可能是旧的")
    print("  - 全部失败时 error message 要清晰，方便 Agent 向用户解释")
    print()

    # ═══════════════════════════════════════════════════════════
    # 第一部分：强制降级演示
    # 打开 _FORCE_FAIL_DEMO 开关，primary & fallback 100% 失败
    # ═══════════════════════════════════════════════════════════
    print("── 阶段1：强制降级演示（primary & fallback 100% 失败）──")
    print()

    global _FORCE_FAIL_DEMO
    _FORCE_FAIL_DEMO = True

    print("  城市      主源      备源      缓存      最终结果")
    print("  ────────  ────────  ────────  ────────  ──────────")
    for city in ["北京", "上海", "吾岸"]:
        result = get_weather_with_fallback(city)
        source = result.get("source", "error")
        print(f"  {city:<8}  {'❌':<8}  {'❌':<8}  "
              f"{'✅' if city in WEATHER_CACHE else '❌':<8}  source={source}")

    _FORCE_FAIL_DEMO = False  # 恢复

    print()
    print("  预期：北京→cache, 上海→cache, 吾岸→error(all_sources_failed)")
    print("  这验证了降级链的 4 级全部被覆盖到了。")

    # ═══════════════════════════════════════════════════════════
    # 第二部分：真实概率的降级测试
    # ═══════════════════════════════════════════════════════════
    print()
    print("── 阶段2：真实概率测试（30% / 10% 失败率）──")
    print("  （多跑几次观察 primary vs fallback 的随机切换）")
    print()

    random.seed(42)
    for i in range(5):
        result = get_weather_with_fallback("北京")
        source = result.get("source", "error")
        print(f"  第{i+1}次: source={source}, "
              f"temp={result.get('temp', '?')}, "
              f"condition={result.get('condition', '?')}")

    # ═══════════════════════════════════════════════════════════
    # 第三部分：Agent 端到端测试（真实概率）
    # ═══════════════════════════════════════════════════════════
    print()
    print("── 阶段3：Agent 端到端测试 ──")
    print("  Agent 调用 get_weather 时，降级链对 LLM 完全透明")
    print()

    run_agent("北京、上海、吾岸，这三地的天气分别怎么样？")

    print()
    print("💡 设计讨论：")
    print("  Agent 需要知道有'降级链'存在吗？")
    print("  还是降级链对 Agent 完全透明更好？")
    print("  各有什么优缺点？")


# ═══════════════════════════════════════════════════════════════
# main 入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请指定任务编号：1 / 2 / 3 / 4")
        print("示例: uv run python code/03-tool-use/tool_error_handling_step3.py 1")
        sys.exit(1)

    task_num = sys.argv[1]
    tasks = {
        "1": task1,
        "2": task2,
        "3": task3,
        "4": task4,
    }

    if task_num not in tasks:
        print(f"无效任务编号: {task_num}，可选: 1/2/3/4")
        sys.exit(1)

    tasks[task_num]()
