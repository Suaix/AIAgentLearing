"""
模块 2 — Step 0 热身：结构化输出（JSON Mode）
直观感受"自由文本"和"结构化 JSON"的本质区别

核心问题：同样的问题，模型能回答正确，但程序怎么"读懂"这个答案？
→ JSON Mode 让 LLM 输出变成可编程的 API

运行方式：
    cd code/02-prompt-engineering
    python json_mode_warmup.py
"""

import os
import json
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
# 实验 1：自由文本 vs JSON 模式 — 信息提取场景
# ══════════════════════════════════════════════════════════════════════

def experiment1_free_text():
    """实验 1A：让模型用自由文本提取结构化信息"""
    print("=" * 60)
    print("📝 实验 1A — 自由文本输出")
    print("=" * 60)

    review = (
        "昨天在海底捞（朝阳大悦城店）吃的晚饭，人均花了 180 元。"
        "点了招牌番茄锅底和牛油辣锅底，虾滑特别弹牙，毛肚也很新鲜。"
        "服务态度一如既往地好，但等位等了 40 分钟。"
        "总体来说还算满意，就是价格小贵。"
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是一个信息提取助手。从用户评论中提取：餐厅名、人均价格、推荐菜（list）、差评点（list）、总体评分（1-5）。"},
            {"role": "user", "content": review},
        ],
        temperature=0.0,
    )
    text_output = response.choices[0].message.content
    print(f"模型输出：\n{text_output}\n")

    # 尝试用程序解析这段文本...
    print("🤔 问题：如果我有 1000 条评论，怎么用程序自动获取「人均价格」字段？")
    print("   → 需要写正则 / 再做一次 NLP 解析，不可靠且成本高\n")


def experiment1_json_mode():
    """实验 1B：用 JSON Mode 提取同样的信息"""
    print("=" * 60)
    print("📝 实验 1B — JSON Mode 输出")
    print("=" * 60)

    review = (
        "昨天在海底捞（朝阳大悦城店）吃的晚饭，人均花了 180 元。"
        "点了招牌番茄锅底和牛油辣锅底，虾滑特别弹牙，毛肚也很新鲜。"
        "服务态度一如既往地好，但等位等了 40 分钟。"
        "总体来说还算满意，就是价格小贵。"
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": (
                "你是一个信息提取助手。从用户评论中提取信息，"
                "并以 JSON 格式输出。\n"
                'JSON 格式：{"restaurant": "...", "avg_price": 数字, '
                '"recommended_dishes": [...], "complaints": [...], "rating": 数字}'
            )},
            {"role": "user", "content": review},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},  # 🔑 关键参数！
    )

    raw = response.choices[0].message.content
    print(f"模型原始输出：\n{raw}\n")

    # 用程序直接解析！
    try:
        data = json.loads(raw)
        print("✅ 程序直接可用！字段访问：")
        print(f"   餐厅名：{data.get('restaurant')}")
        print(f"   人均价格：{data.get('avg_price')} 元")
        print(f"   推荐菜：{data.get('recommended_dishes')}")
        print(f"   差评点：{data.get('complaints')}")
        print(f"   评分：{data.get('rating')}/5")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败：{e}")


# ══════════════════════════════════════════════════════════════════════
# 实验 2：JSON Mode 的"潜规则"——提示词中必须包含 "json" 字样
# ══════════════════════════════════════════════════════════════════════

def experiment2_json_keyword_required():
    """实验 2：DeepSeek JSON Mode 要求 prompt 中出现 'json' 字样"""
    print("\n" + "=" * 60)
    print("📝 实验 2 — JSON Mode 要求 prompt 中包含 'json' 关键字")
    print("=" * 60)

    # 两个对比：一个提示词不含 "json"，一个包含
    test_cases = [
        ("不含 'json' 关键字", "列出 3 种编程语言及其主要用途。"),
        ("含 'json' 关键字", "列出 3 种编程语言及其主要用途。请以 JSON 格式输出。"),
    ]

    for label, prompt in test_cases:
        print(f"\n--- {label} ---")
        print(f"  提示词：{prompt}")
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=512,
            )
            content = response.choices[0].message.content
            print(f"  输出：{content[:200]}...")
            # 尝试解析
            try:
                json.loads(content)
                print("  ✅ 是合法 JSON")
            except json.JSONDecodeError:
                print("  ⚠️ 不是合法 JSON（可能因为提示词不含 'json'）")
        except Exception as e:
            print(f"  ❌ API 报错：{e}")


# ══════════════════════════════════════════════════════════════════════
# 实验 3：JSON Mode 的边界 — 合法 JSON ≠ 符合你的 Schema
# ══════════════════════════════════════════════════════════════════════

def experiment3_schema_not_guaranteed():
    """实验 3：JSON Mode 保证合法 JSON，但不保证字段名/类型完全一致"""
    print("\n" + "=" * 60)
    print("📝 实验 3 — JSON Mode 的边界：合法 JSON ≠ 符合 Schema")
    print("=" * 60)

    # 故意给一个模糊的 schema 描述
    prompt = (
        "描述一下 Python 语言的特点。输出 JSON。"
    )
    # 不给具体字段名，看模型会用什么 key

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,  # 用一点随机性看字段变化
        response_format={"type": "json_object"},
        max_tokens=512,
    )

    raw = response.choices[0].message.content
    print(f"模型输出：\n{raw}\n")

    try:
        data = json.loads(raw)
        print(f"实际字段名：{list(data.keys())}")
        print("💡 结论：模型自己决定字段名——如果没有在 prompt 中明确要求的话")
        print("   → 生产环境中需要客户端做 Schema 校验（Pydantic / JSON Schema）")
    except json.JSONDecodeError as e:
        print(f"❌ 解析失败：{e}")


# ══════════════════════════════════════════════════════════════════════
# 实验 4：实战场景 — 批量评论分析与 JSON 容错
# ══════════════════════════════════════════════════════════════════════

def experiment4_batch_review_analysis():
    """实验 4：模拟批量处理 + 容错机制"""
    print("\n" + "=" * 60)
    print("📝 实验 4 — 实战：批量评论分析 + JSON 容错")
    print("=" * 60)

    reviews = [
        "这家店的披萨太好吃了，芝士拉丝超长！就是上菜慢了点。",
        "服务态度极差，等了半小时没人理，再也不来了。",
        "性价比很高，学生党友好。炸鸡外酥里嫩，推荐！",
    ]

    success_count = 0
    fail_count = 0

    for i, review in enumerate(reviews, 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": (
                        "分析用户评论的情感（正面/负面/中性），提取关键词。\n"
                        '输出 JSON 格式：{"sentiment": "正面/负面/中性", '
                        '"keywords": [...], "confidence": 0.0-1.0}'
                    )},
                    {"role": "user", "content": review},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=256,
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)
            print(f"\n评论 {i}：「{review}」")
            print(f"  → 情感：{data.get('sentiment')}，关键词：{data.get('keywords')}，置信度：{data.get('confidence')}")
            success_count += 1

        except json.JSONDecodeError:
            print(f"\n评论 {i}：「{review}」→ ❌ JSON 解析失败")
            fail_count += 1
        except Exception as e:
            print(f"\n评论 {i}：「{review}」→ ❌ API 错误：{e}")
            fail_count += 1

    print(f"\n📊 批量处理结果：成功 {success_count}/{len(reviews)}，失败 {fail_count}/{len(reviews)}")


# ══════════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🚀 模块 2 · 结构化输出（JSON Mode）— Step 0 热身运行\n")
    print("核心问题：模型能回答正确，但程序怎么「读懂」答案？\n")

    experiment1_free_text()
    experiment1_json_mode()
    experiment2_json_keyword_required()
    experiment3_schema_not_guaranteed()
    experiment4_batch_review_analysis()

    print("\n" + "=" * 60)
    print("🎯 Step 0 热身完成！关键观察点：")
    print("  1. 自由文本 vs JSON：哪个能被代码直接消费？")
    print("  2. response_format={'type': 'json_object'} 的作用是什么？")
    print("  3. JSON Mode 保证什么？不保证什么？")
    print("  4. 生产环境中还需要什么额外措施？")
    print("=" * 60)
