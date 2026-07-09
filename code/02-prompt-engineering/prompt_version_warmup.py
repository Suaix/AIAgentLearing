"""
模块 2 — Step 0 热身：Prompt 版本管理
直观感受「硬编码 Prompt」的维护噩梦 vs 「模板化 + 配置分离」的工程化方案

核心问题：Prompt 不是写完就完了——它需要迭代、对比、回滚。
→ 当你有 10 个 Agent、每个有 3 个 Prompt 版本时，怎么管？

运行方式：
    cd code/02-prompt-engineering
    uv run python prompt_version_warmup.py
"""

import os
import json
import httpx
from datetime import datetime
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
# 实验 1：硬编码 Prompt 的维护灾难（问题演示）
# ══════════════════════════════════════════════════════════════════════

def experiment1_hardcoded_chaos():
    """展示没有版本管理时，多处硬编码 Prompt 的典型问题"""
    print("=" * 60)
    print("📝 实验 1 — 硬编码 Prompt 的三大痛点")
    print("=" * 60)

    # 场景：你的项目中有 3 个地方用到了"客服回复"Prompt，
    # 分别在不同的文件里，被人手动改过，现在不知道哪个是"最新版"

    # 痛点 1：不知道哪个版本是最新的
    prompt_v1 = "你是一个客服助手，回答用户的问题。语气友好。"
    prompt_v2 = "你是一个专业的客服代表。使用礼貌、正式的语言回复客户。回答长度不超过100字。"
    prompt_v3 = "你是客服助手。友好回答。不要提及其他品牌。"

    print("\n🔴 痛点 1：同一个 Prompt 散落在 3 个文件中，分别被不同人改过")
    print(f"  api_handler.py:    {prompt_v1}")
    print(f"  bot_service.py:    {prompt_v2}")
    print(f"  legacy_worker.py:  {prompt_v3}")
    print("  → 哪个是正式的「客服 Prompt」？没人知道。")

    # 痛点 2：改了一个 Prompt，忘了改另一个
    print("\n🔴 痛点 2：需要全局更新 Prompt 时（如品牌改名），漏改了某个文件")
    print("  → 线上出现两种风格的回复，用户体验不一致")

    # 痛点 3：出问题时找不到历史版本回滚
    print("\n🔴 痛点 3：改了 Prompt 之后效果变差，想回滚到上一版")
    print("  → 没存历史版本，只能凭记忆恢复，或者从 Git log 里翻")


# ══════════════════════════════════════════════════════════════════════
# 实验 2：最简单的版本管理 — JSON 配置 + 变量模板
# ══════════════════════════════════════════════════════════════════════

# 这就是版本管理的核心数据结构
PROMPT_REGISTRY = {
    "customer_service": {
        "v1.0": {
            "created": "2026-06-01",
            "author": "summer",
            "status": "deprecated",  # 已废弃
            "system": "你是一个客服助手。用友好的语气回答用户问题。",
        },
        "v1.1": {
            "created": "2026-07-01",
            "author": "summer",
            "status": "deprecated",
            "system": (
                "你是一个客服助手。使用友好、专业的语气。"
                "回答不超过 150 字。"
            ),
        },
        "v2.0": {
            "created": "2026-07-09",
            "author": "summer",
            "status": "active",  # 当前生效
            "system": (
                "你是{company_name}的智能客服。\n\n"
                "## 行为规则\n"
                "1. 使用友好、简洁的语言（每条回复不超过 150 字）\n"
                "2. 只回答与{product_domain}相关的问题\n"
                "3. 如果用户不满意，主动提供转人工客服的方式\n"
                "4. 不要提及其他竞争品牌\n\n"
                "## 回复格式\n"
                "以「您好！👋」开头，以「还有其他问题吗？」结尾"
            ),
            "variables": ["company_name", "product_domain"],
        },
    },
    "code_reviewer": {
        "v1.0": {
            "created": "2026-07-01",
            "author": "summer",
            "status": "active",
            "system": (
                "你是{reviewer_style}的代码审查员。\n"
                "审查代码时关注：{focus_areas}\n"
                "用不超过{max_suggestions}条建议的形式输出。"
            ),
            "variables": ["reviewer_style", "focus_areas", "max_suggestions"],
        },
    },
}


def experiment2_prompt_registry():
    """演示集中化 Prompt 注册表的使用"""
    print("\n" + "=" * 60)
    print("📝 实验 2 — Prompt Registry（集中化版本管理）")
    print("=" * 60)

    # 获取客服 Prompt 的最新版本
    cs_config = PROMPT_REGISTRY["customer_service"]
    latest_version = max(cs_config.keys())
    active_prompt = cs_config[latest_version]

    print(f"📋 客服 Prompt 当前版本：{latest_version}（状态：{active_prompt['status']}）")
    print(f"   创建时间：{active_prompt['created']}")
    print(f"   变量列表：{active_prompt.get('variables', [])}")
    print(f"\n   System Prompt 模板：\n{active_prompt['system'][:200]}...")

    # 填充变量
    variables = {
        "company_name": "快乐书店",
        "product_domain": "书籍和阅读",
    }
    filled_prompt = active_prompt["system"].format(**variables)
    print(f"\n   ✅ 填充变量后的实际 Prompt：\n{filled_prompt}")

    # 展示版本历史
    print(f"\n📜 客服 Prompt 版本历史：")
    for ver, config in sorted(cs_config.items()):
        status_icon = "🟢" if config["status"] == "active" else "⚫"
        print(f"   {status_icon} {ver} ({config['created']}) — {config['status']} — 作者：{config['author']}")


# ══════════════════════════════════════════════════════════════════════
# 实验 3：实战 — 用 Registry 模式调用 API
# ══════════════════════════════════════════════════════════════════════

def experiment3_registry_in_action():
    """展示 Prompt Registry 在实际 API 调用中的使用"""
    print("\n" + "=" * 60)
    print("📝 实验 3 — 实战：Registry 驱动的 API 调用")
    print("=" * 60)

    # 模拟：你需要用两个不同版本的客服 Prompt 回复同一个问题
    # 来对比 A/B 测试效果
    user_msg = "你们店里有没有《三体》这本书？价格多少？"

    cs_config = PROMPT_REGISTRY["customer_service"]
    variables = {"company_name": "快乐书店", "product_domain": "书籍和阅读"}

    for version in ["v1.1", "v2.0"]:
        prompt_config = cs_config[version]
        system_prompt = prompt_config["system"].format(**variables)

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        answer = response.choices[0].message.content
        print(f"\n--- {version} ({prompt_config['status']}) ---")
        print(f"  回复：{answer[:200]}")

    print("\n💡 A/B 测试的关键：同一份 Registry 里存放多个版本，切换只需改一行代码。")
    print("   不需要在代码里搜索-替换 Prompt 字符串。")


# ══════════════════════════════════════════════════════════════════════
# 实验 4：版本对比工具 — 看两个 Prompt 版本之间改了什么
# ══════════════════════════════════════════════════════════════════════

def experiment4_diff():
    """简单的版本 Diff 工具"""
    print("\n" + "=" * 60)
    print("📝 实验 4 — Prompt 版本 Diff")
    print("=" * 60)

    cs = PROMPT_REGISTRY["customer_service"]
    old_sp = cs["v1.1"]["system"]
    new_sp = cs["v2.0"]["system"]

    # 简单的逐行对比
    old_lines = set(old_sp.split("\n"))
    new_lines = set(new_sp.split("\n"))

    added = new_lines - old_lines
    removed = old_lines - new_lines

    print(f"📊 v1.1 → v2.0 的变更：")
    if added:
        print(f"  ➕ 新增 {len(added)} 行：")
        for line in sorted(added):
            if line.strip():
                print(f"     + {line.strip()}")
    if removed:
        print(f"  ➖ 删除 {len(removed)} 行：")
        for line in sorted(removed):
            if line.strip():
                print(f"     - {line.strip()}")

    print("\n💡 关键变更：v2.0 引入了变量模板（{company_name}、{product_domain}），")
    print("   让同一个 Prompt 可以适配不同的业务场景，无需复制粘贴。")


# ══════════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🚀 模块 2 · Prompt 版本管理 — Step 0 热身运行\n")
    print("核心问题：当 Prompt 从「一段文本」变成「项目资产」，怎么管理？\n")

    experiment1_hardcoded_chaos()
    experiment2_prompt_registry()
    experiment3_registry_in_action()
    experiment4_diff()

    print("\n" + "=" * 60)
    print("🎯 Step 0 热身完成！关键观察点：")
    print("  1. 硬编码 Prompt 的三个痛点是什么？")
    print("  2. Prompt Registry 的核心数据结构是什么？（嵌套 dict + version key）")
    print("  3. 变量模板（{variable}）解决了什么问题？")
    print("  4. 版本号（v1.0 / v2.0）和状态标记（active / deprecated）有什么用？")
    print("=" * 60)
