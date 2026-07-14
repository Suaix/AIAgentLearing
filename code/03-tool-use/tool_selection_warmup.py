"""
模块 3：Tool Use / Function Calling — 子主题 3：Tool 选择策略 — Step 0 热身
==============================================================================

演示 Tool Use 中的三个控制开关：
  - tool_choice="auto"    → LLM 自主决定调不调工具（默认行为）
  - tool_choice="required" → 强制 LLM 必须调工具（不能纯文本回答）
  - tool_choice="none"     → 禁止 LLM 调工具（只能纯文本回答）
  - parallel_tool_calls=False → 禁止并行，即使两个工具互不依赖也分两轮调

运行方式：
  uv run python code/03-tool-use/tool_selection_warmup.py
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
MODEL = "deepseek-v4-flash"


# ── Mock 工具 ──

def get_weather(city: str) -> str:
    data = {"北京": {"天气": "晴", "温度": "28°C"}, "上海": {"天气": "阴", "温度": "25°C"}}
    return json.dumps(data.get(city, {"天气": "未知"}), ensure_ascii=False)


def get_time() -> str:
    from datetime import datetime
    return json.dumps({"当前时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "获取当前系统时间",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TOOL_MAP = {"get_weather": get_weather, "get_time": get_time}


def run_demo(label: str, query: str, **api_kwargs):
    """运行一次演示，打印工具调用过程和最终回答"""
    print(f"\n{'─' * 55}")
    print(f"  {label}")
    print(f"  查询：{query}")
    if api_kwargs:
        print(f"  参数：{api_kwargs}")
    print(f"{'─' * 55}")

    messages = [{"role": "user", "content": query}]
    for turn in range(1, 4):
        # DeepSeek: thinking mode 不支持 tool_choice="required"/"none"
        # 当使用这些参数时，需要关闭 thinking
        extra = {}
        if api_kwargs.get("tool_choice") in ("required", "none"):
            extra["extra_body"] = {"thinking": {"type": "disabled"}}
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, **api_kwargs, **extra
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            names = [tc.function.name for tc in msg.tool_calls]
            print(f"  [轮{turn}] 🔧 {len(msg.tool_calls)} 个工具调用：{names}")
            # 追加 assistant 消息（含 tool_calls）
            tmp = msg.model_dump()
            # 用 model_dump 保留 tool_calls 结构后 append
            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                result = TOOL_MAP[tc.function.name](**args)
                print(f"    → {tc.function.name}({json.dumps(args, ensure_ascii=False)}) = {result}")
                messages.append({
                    "role": "tool", "tool_call_id": tc.id, "content": result,
                })
            continue
        print(f"  📝 回答：{msg.content[:150]}{'...' if len(msg.content or '') > 150 else ''}")
        break
    else:
        print("  ⚠️ 轮次耗尽")


def main():
    print("=" * 55)
    print("  模块 3-3：Tool 选择策略 — Step 0 热身")
    print("=" * 55)

    # ── 演示 ①：默认 auto — LLM 自由选择 ──
    run_demo(
        '演示① tool_choice="auto"（默认）— LLM 自主决定',
        "现在几点了？",
    )

    # ── 演示 ②：force required — 强制调工具 ──
    run_demo(
        '演示② tool_choice="required" — 强制必须调工具',
        "今天天气真好，适合出去玩吗？",
        tool_choice="required",
    )
    # 注意：即使用户没要求查天气，LLM 也被迫找一个工具调用

    # ── 演示 ③：force none — 禁止调工具 ──
    run_demo(
        '演示③ tool_choice="none" — 禁止调工具',
        "帮我查一下北京天气",
        tool_choice="none",
    )
    # 注意：即使用户要求查天气，LLM 也不能调工具，只能"假装"回答

    # ── 演示 ④：禁止并行 — 两个独立查询也要分两轮 ──
    run_demo(
        "演示④ parallel_tool_calls=False — 禁止并行",
        "北京和上海天气分别怎么样？",
        parallel_tool_calls=False,
    )
    # 对比之前 warmup 演示②：相同查询，默认并行一次调两个，这里分两轮

    print(f"\n{'=' * 55}")
    print("  关键观察点：")
    print("  ① tool_choice='required' 时，LLM 被迫调了哪个工具？合理吗？")
    print("  ② tool_choice='none' 时，LLM 能查天气吗？它怎么回答的？")
    print("  ③ parallel_tool_calls=False 时，同样的查询多消耗了几轮？")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
