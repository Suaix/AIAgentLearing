from ast import List
from concurrent.futures import ThreadPoolExecutor
import json
import os
from random import Random
import random
import time
from typing import Callable

from dotenv import load_dotenv
from numpy.random import f
from openai import OpenAI
from mock_data import search_kb_lookup, paper_db_query

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)

MODEL = "deepseek-v4-flash"
RETRY_CONFIG = {
    "timeout": 5.0,  # 单个工具调用的超时时间（秒）
    "max_retries": 3,  # 同一工具最大重试次数
    "max_turns": 10,  # Agent 循环最大轮数
}


def web_search(query: str) -> dict:
    if random.random() <= 0.3:
        time.sleep(5)
        return {"error": "timeout", "message": "call web search timeout"}
    result = search_kb_lookup(query)

    if result:
        return {"status": "ok", "query": query, "results": json.dumps(result)}

    return {"error": "no_result", "message": "未查询到相关信息"}


def calcuator(expression: str) -> dict:
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
        return {"error": "syntax_error", "message": str(e)}


def paper_db(query: str) -> dict:
    try:
        raws = paper_db_query(query)
        return {"status": "ok", "rows": raws, "count": len(raws)}
    except PermissionError as e1:
        return {"error": "permission_error", "message": str(e1)}
    except ValueError as e2:
        return {"error": "value_error", "message": str(e2)}
    except Exception as e:
        return {"error": "common_error", "message": str(e)}


web_search_tool = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "互联网搜索引擎，搜索关键词返回搜索结果。搜索词最好控制在50字以内。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
            },
            "required": ["query"],
        },
    },
}

calculator_tool = {
    "type": "function",
    "function": {
        "name": "calcuator",
        "description": "计算数学表达式，如：1+2+3。",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "计算表达式"},
            },
            "required": ["expression"],
        },
    },
}

paper_db_tool = {
    "type": "function",
    "function": {
        "name": "paper_db",
        "description": "查询论文数据库获取论文信息",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "数据库查询语句，不支持DROP/DELETE操作，数据库",
                },
            },
            "required": ["query"],
        },
    },
}

TOOLS_LIST = [web_search_tool, calculator_tool, paper_db_tool]
TOOLS_MAP = {"web_search": web_search, "calcuator": calcuator, "paper_db": paper_db}


def call_with_timeout(
    func: Callable, kwargs: dict, timeout: float = 5.0, funname: str = ""
) -> dict:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, **kwargs)
        try:
            result = future.result(timeout=timeout)
            return result
        except TimeoutError:
            return {"error": "timeout", "message": "{funname} call timeout"}
        finally:
            executor.shutdown()


def run_agent(user_message: str, config: dict | None = None):
    print(f"*" * 60)
    print(f"开始处理问题：{user_message}")
    print(f"*" * 60)
    system_prompt = """'
    你是一个有用的智能研究助手，协助用户完成指定课题的研究工作。
    行为准则：
    1. 调用工具遇到异常时仔细阅读异常信息，尝试其他方式调用。
    2. 每个工具失败后最多调用2次，不要死循环地调用。
    3. 如果错误信息展示了替代方案，尝试替代方案。
    """
    msg_list: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    tools_call_record: dict[str, int] = {}

    cfg = config or RETRY_CONFIG
    print(f"cfg={cfg}")
    timeout = cfg["timeout"]
    maxturns = cfg["max_turns"]
    maxretries = cfg["max_retries"]

    for turn in range(1, maxturns + 1):
        print(f"第 {turn} 轮调用")
        response = client.chat.completions.create(
            model=MODEL, messages=msg_list, tool_choice="auto", tools=TOOLS_LIST
        )
        message = response.choices[0].message
        print(f"assistant:{message.content}")
        if not message.tool_calls:
            msg_list.append({"role": "assistant", "content": message.content})
            break

        msg_list.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            }
        )

        for tc in message.tool_calls:
            funname = tc.function.name
            kwargs = json.loads(tc.function.arguments)
            print(f"call tool: funname={funname}, kwargs={kwargs}")
            func = TOOLS_MAP[funname]
            if func:
                result = call_with_timeout(
                    func, kwargs, timeout=timeout, funname=funname
                )
            else:
                result = {"error": "error_tool_call", "message": "unknown tool call"}

            print(f"tool result:{json.dumps(result)[:100]}")
            msg_list.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
            if "error" in result:
                tools_call_record[funname] = tools_call_record.get(funname, 0) + 1
                print(
                    f"{funname}第{tools_call_record[funname]}次调用失败， result为{json.dumps(result)[:100]}"
                )
                if tools_call_record[funname] >= maxretries:
                    print(f"{funname} 工具调用重试次数已超最大限制")
            else:
                tools_call_record[funname] = 0
    print(f"=" * 60)


if __name__ == "__main__":
    user_msgs = [
        "近三年AI大模型参数量增长了大约多少倍？帮我搜索相关数据并计算。",
        "帮我查一下Transformer和Mamba两篇论文的关键数据，  算一下Transformer的参数量是Mamba的多少倍。",
        "查询 ResNet 论文，然后帮我算一下 100÷0。",
    ]
    config = {
        "timeout": 5.0,
        "max_turns": 10,
        "max_retries": 2,
    }
    for msg in user_msgs:
        run_agent(msg, config=config)
