"""
Step 3 精简练习：模型选型 + 成本估算
====================================
两个场景下的模型选型决策练习。
"""

# ═══════════════════════════════════════════════════════════
# 练习 1：选型决策
# ═══════════════════════════════════════════════════════════

print("=" * 60)
print("练习 1：选型决策 — 给以下 3 个场景选模型并说明理由")
print("=" * 60)

SCENARIOS = [
    {
        "name": "客服机器人",
        "desc": "电商网站的自动客服。用户问'我的快递到哪了'，系统查询物流 API 后生成回复。每天约 50 万次对话。",
        "constraints": "高并发、低延迟(<1s)、成本敏感"
    },
    {
        "name": "合同审查助手",
        "desc": "律师事务所内部工具。上传 80 页 PDF 合同，AI 标注风险条款。每天处理约 50 份合同。",
        "constraints": "长文档处理、高准确率、数据绝不能外泄、成本不敏感"
    },
    {
        "name": "个人学习助手",
        "desc": "就是你当前用的这个项目。一个人用，偶尔问问题、生成笔记。大部分是中文交互。",
        "constraints": "中文好、支持长上下文、一个人用成本怎么都高不到哪去"
    },
]

# TODO ①：对每个场景，从下面 4 个选项中选一个最合适的模型
OPTIONS = [
    "A. Claude Opus 4.8（旗舰，贵）",
    "B. DeepSeek V3（性价比，中文好）",
    "C. GPT-4o-mini（便宜，快）",
    "D. Llama 4 自部署（数据不出网，免费但需运维）",
]

for i, s in enumerate(SCENARIOS, 1):
    print(f"\n场景 {i}：{s['name']}")
    print(f"  需求：{s['desc']}")
    print(f"  约束：{s['constraints']}")
    print(f"  可选：{', '.join(OPTIONS)}")
    # 选择在练习 2 的成本估算后统一执行

# ═══════════════════════════════════════════════════════════
# 练习 2：成本估算
# ═══════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print("练习 2：成本估算 — 用选型四问框架，算一下真实花费")
print("=" * 60)

# 模型价格（已声明，用于计算）
PRICES = {
    "Claude Opus 4.8":   {"input": 15.0, "output": 75.0},
    "GPT-4o":            {"input": 2.50, "output": 10.0},
    "DeepSeek V3":       {"input": 0.27, "output": 1.10},
    "GPT-4o-mini":       {"input": 0.15, "output": 0.60},
}

# ─── 场景 A：客服机器人（每天 50 万次对话）───
print(f"\n📊 场景 A：客服机器人成本估算")
daily_convos = 500_000
tokens_per_convo_in = 100    # 用户输入（"我的快递到哪了" + 上下文）
tokens_per_convo_out = 80    # AI 回复（"您的快递已到达XX站点，预计今天送达"）

print(f"  每天对话量：{daily_convos:,} 次")
print(f"  每次对话 Token：~{tokens_per_convo_in} in + {tokens_per_convo_out} out")

daily_tokens_in = daily_convos * tokens_per_convo_in
daily_tokens_out = daily_convos * tokens_per_convo_out
print(f"  每天总 Token：{daily_tokens_in:,} in + {daily_tokens_out:,} out")

# TODO ②：计算如果用 DeepSeek V3 每天要花多少钱？
print(f"\n  ┌─ 每日成本估算 ──────────────────────┐")
for name, price in PRICES.items():
    daily_cost = (daily_tokens_in * price["input"] + daily_tokens_out * price["output"]) / 1_000_000
    monthly_cost = daily_cost * 30
    print(f"  │ {name:<18} ${daily_cost:>8.2f}/天   ${monthly_cost:>10,.0f}/月 │")
print(f"  └──────────────────────────────────────┘")

# ─── 场景 B：合同审查（每天 50 份）───
print(f"\n📊 场景 B：合同审查助手成本估算")
daily_docs = 50
tokens_per_doc_in = 80_000    # 80 页 PDF ≈ 80K tokens
tokens_per_doc_out = 2_000    # 审查意见
# 注意：每次对话累积上下文 → 可能超出 Context Window！

print(f"  每天合同数：{daily_docs} 份")
print(f"  每份合同 Token：~{tokens_per_doc_in:,} in + ~{tokens_per_doc_out:,} out")

daily_tokens_in_b = daily_docs * tokens_per_doc_in
daily_tokens_out_b = daily_docs * tokens_per_doc_out
print(f"  单份合同 Token 数：{tokens_per_doc_in:,} → 注意！检查是否超出各模型的 Context Window")
print(f"    GPT-4o: 128K ✅  |  DeepSeek V3: 128K ✅")
print(f"    Claude Opus: 200K ✅  |  GPT-4o-mini: 128K ✅")

print(f"\n  ┌─ 每日成本估算 ──────────────────────┐")
for name, price in PRICES.items():
    daily_cost = (daily_tokens_in_b * price["input"] + daily_tokens_out_b * price["output"]) / 1_000_000
    monthly_cost = daily_cost * 30
    print(f"  │ {name:<18} ${daily_cost:>8.2f}/天   ${monthly_cost:>10,.0f}/月 │")
print(f"  └──────────────────────────────────────┘")

# ─── 场景 C：个人学习助手 ────
print(f"\n📊 场景 C：个人学习助手成本估算")
daily_tokens_in_c = 5_000     # 一天提的问题
daily_tokens_out_c = 10_000   # AI 回复
# 包括笔记生成、代码解释、概念讨论

print(f"  每天约 {daily_tokens_in_c:,} tokens 输入 + {daily_tokens_out_c:,} tokens 输出")

print(f"\n  ┌─ 每日成本估算 ──────────────────────┐")
for name, price in PRICES.items():
    daily_cost = (daily_tokens_in_c * price["input"] + daily_tokens_out_c * price["output"]) / 1_000_000
    monthly_cost = daily_cost * 30
    print(f"  │ {name:<18} ${daily_cost:>6.4f}/天   ${monthly_cost:>8.2f}/月 │")
print(f"  └──────────────────────────────────────┘")


# ═══════════════════════════════════════════════════════════
# 综合决策
# ═══════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print("📋 你的选型决策（TODO ① 回答）")
print("=" * 60)

print("""
对 3 个场景做出选择，在每个 TODO 位置填入你选择的选项字母（A/B/C/D）：

场景 1 — 客服机器人：
  我选 [___]，理由：__________________________________

场景 2 — 合同审查助手：
  我选 [___]，理由：__________________________________

场景 3 — 个人学习助手：
  我选 [___]，理由：__________________________________
""")

print("=" * 60)
print("✅ 练习就绪，完成决策后告诉我你的选择和理由。")
print("=" * 60)
