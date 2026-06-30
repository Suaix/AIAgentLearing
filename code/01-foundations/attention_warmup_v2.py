"""
Step 0 热身（v2）：Self-Attention 直观演示 — 让你"看见"注意力
==============================================================
重新设计：使用手工设计的数据，而不是随机数。
目标：看到有意义的 Attention Pattern——哪个词在关注哪个词。

句子：「猫 追 老鼠」
直觉：  "追"应该同时关注"猫"（谁在追）和"老鼠"（追什么）
        "老鼠"应该关注"追"（被怎么了）
"""

import numpy as np

print("=" * 60)
print("🐱 Self-Attention 直观演示：「猫 追 老鼠」")
print("=" * 60)

# ═══════════════════════════════════════════════════════════
# 1. 什么是 Embedding？把词变成数字向量
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("第 1 步：Embedding — 每个词 → 一个数字向量")
print("─" * 60)
print()
print("计算机不认识「猫」这个汉字，只认识数字。")
print("所以第一步：把每个词翻译成一个数字列表（向量）。")
print()
print("我们给每个词分配 5 个维度的语义特征：")
print()

# 手工设计 embedding，让语义相近的词向量也相近
embeddings = {
    "猫":   np.array([1.0, 0.8, 0.1, 0.2, 0.3]),   # 动物特征高
    "追":   np.array([0.2, 0.3, 0.9, 0.8, 0.2]),   # 动作特征高
    "老鼠": np.array([0.9, 0.7, 0.1, 0.2, 0.4]),   # 动物特征高（和猫接近！）
}

feature_names = ["动物性", "大小", "动作性", "力度", "情感"]

print(f"          {'  '.join(f'{n:^6}' for n in feature_names)}")
for word, vec in embeddings.items():
    vals = "  ".join(f"{v:^6.1f}" for v in vec)
    print(f"  {word:^4}  [{vals}]")

print()
print("👀 观察：「猫」和「老鼠」的「动物性」维度都很高（1.0 vs 0.9）")
print("         而「追」的「动作性」维度很高（0.9）")
print("         这说明向量已经捕捉到了语义相似性！")

# ═══════════════════════════════════════════════════════════
# 2. 直观类比：图书馆检索系统
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("第 2 步：Self-Attention 的直观类比")
print("─" * 60)
print()
print("想象你在图书馆找书：")
print()
print("  你心里的需求          = Query（查询）")
print("  书架上的标签          = Key（索引）")
print("  书的实际内容          = Value（内容）")
print()
print("  过程：你拿 Query 去比对每个 Key → 越匹配越关注 → 取对应的 Value")
print()
print("Self-Attention 做的是一样的事：")
print("  每个词发出一个 Query（我想找什么相关信息）")
print("  每个词贴一个 Key（我是什么类型的信息）")
print("  每个词存储一个 Value（我的实际语义内容）")
print()

# 用具体的例子说明
print("  具体例子 — 句子「猫 追 老鼠」：")
print("  ┌──────────────────────────────────────────────┐")
print("  │ 「追」的 Query = [动作性强, 需要主语和宾语]  │")
print("  │ 「猫」的 Key   = [动物, 可以是主语]          │")
print("  │ 「老鼠」的 Key = [动物, 可以是宾语]          │")
print("  │                                              │")
print("  │ 匹配结果：                                    │")
print("  │   Query_追 · Key_猫   = 高 → 关注「猫」      │")
print("  │   Query_追 · Key_老鼠 = 高 → 关注「老鼠」    │")
print("  └──────────────────────────────────────────────┘")

# ═══════════════════════════════════════════════════════════
# 3. 用真实矩阵计算来演示
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("第 3 步：手工计算一遍 Self-Attention")
print("─" * 60)

# 构建输入矩阵 X（3个词 × 5维）
tokens = ["猫", "追", "老鼠"]
X = np.array([embeddings[t] for t in tokens])

print(f"\n  X (输入): {X.shape} — 3个词，每个5维")
print()

# 手工设计 Q/K/V 权重，让「追」去关注「猫」和「老鼠」
# W_Q: 把动作性高的词变成"我需要找名词"的查询
# W_K: 把动物性高的词变成"我是名词实体"的标签
# W_V: 保留原始语义

np.random.seed(42)
d_model = 5
d_k = 3

# 手工设计权重（不是随机的！），让「追」关注两个名词
W_Q = np.array([
    [0.1,  0.1,  0.5],   # 维度0「动物性」→ 低查询权重
    [0.1,  0.1,  0.2],   # 维度1「大小」→ 低查询权重
    [0.8,  0.3,  0.1],   # 维度2「动作性」→ 高查询权重！动词发出查询
    [0.7,  0.2,  0.1],   # 维度3「力度」→ 较高查询权重
    [0.1,  0.8,  0.3],   # 维度4「情感」→ 中等查询权重
])

W_K = np.array([
    [0.9,  0.2,  0.1],   # 维度0「动物性」→ 高键权重！名词响应查询
    [0.7,  0.1,  0.1],   # 维度1「大小」
    [0.1,  0.1,  0.8],   # 维度2「动作性」→ 低键权重（动词不响应）
    [0.1,  0.1,  0.7],   # 维度3「力度」
    [0.2,  0.9,  0.2],   # 维度4「情感」
])

W_V = np.array([
    [0.8,  0.1,  0.1],
    [0.7,  0.1,  0.1],
    [0.1,  0.8,  0.1],
    [0.1,  0.7,  0.1],
    [0.1,  0.1,  0.8],
])

# 计算 Q, K, V
Q = X @ W_Q
K = X @ W_K
V = X @ W_V

print("  投影后的 Q (Query, 每个词的「查询」):")
for i, t in enumerate(tokens):
    print(f"    Q_{t}: {np.round(Q[i], 3)}")
print()
print("  投影后的 K (Key, 每个词的「标签」):")
for i, t in enumerate(tokens):
    print(f"    K_{t}: {np.round(K[i], 3)}")
print()

# 计算注意力分数
scores = Q @ K.T
scaled_scores = scores / np.sqrt(d_k)

print("  注意力分数矩阵 (Q·K^T / √3):")
print(f"            {'猫':>8}  {'追':>8}  {'老鼠':>8}")
for i, t_i in enumerate(tokens):
    row = "  ".join(f"{scaled_scores[i][j]:8.3f}" for j in range(len(tokens)))
    print(f"    {t_i}  →  {row}")

# Softmax
def softmax(x):
    exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=1, keepdims=True)

attention = softmax(scaled_scores)

# ═══════════════════════════════════════════════════════════
# 4. 可视化注意力模式
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("第 4 步：注意力权重 — 谁在关注谁？")
print("─" * 60)
print()

# 可视化热力图
print("        关注目标 →")
print("         " + "      ".join(f"{t:^6}" for t in tokens))
print("        " + "─" * 30)
for i, t_i in enumerate(tokens):
    bars = "  ".join(f"{attention[i][j]:.3f}" for j in range(len(tokens)))
    print(f"  {t_i}  |  {bars}")
print("  ↑")
print("  查询者")

# 文本解读
print()
print("  🔍 关键发现：")
for i, t_i in enumerate(tokens):
    max_idx = np.argmax(attention[i])
    max_val = attention[i][max_idx]
    print(f"  「{t_i}」最关注的是 → 「{tokens[max_idx]}」（权重 {max_val:.3f}）")

# 特别解读「追」的注意力
print(f"\n  📖 详细解读「追」的注意力分布：")
for j, t_j in enumerate(tokens):
    bar_len = int(attention[1][j] * 40)
    bar = "█" * bar_len
    print(f"     对「{t_j}」: {attention[1][j]:.3f} {bar}")
print(f"\n  → 「追」同时关注主语「猫」和宾语「老鼠」，")
print(f"    因为动词需要知道「谁在做」和「谁在被做」！")

# ═══════════════════════════════════════════════════════════
# 5. 最终输出 — 融合上下文的新表示
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("第 5 步：输出 — 融合了上下文信息的新向量")
print("─" * 60)
print()

# Attention 输出再通过一个输出投影 W_O 映射回原始维度
# 在实际 Transformer 中，Multi-Head Attention 后面都有这个投影
W_O = np.array([
    [0.6,  0.3,  0.1,  0.1,  0.2],
    [0.3,  0.5,  0.2,  0.1,  0.1],
    [0.1,  0.2,  0.5,  0.4,  0.3],
])

output = attention @ V @ W_O  # (3,3) × (3,5) = (3,5) — 回到原始维度

for i, t_i in enumerate(tokens):
    print(f"  「{t_i}」的原始 embedding:   {np.round(X[i], 3)}")
    print(f"  「{t_i}」的 attention 输出:  {np.round(output[i], 3)}")
    # 计算变化幅度
    change = np.linalg.norm(output[i] - X[i])
    print(f"           变化幅度: {change:.3f}")
    print()

print("  💡 关键洞察：")
print("  ┌────────────────────────────────────────────────────┐")
print("  │ Attention 的输出 ≠ 原始 embedding                  │")
print("  │ 输出 = 原始信息 + 从上下文「借来」的信息             │")
print("  │                                                    │")
print("  │ 「追」的输出包含了「猫」（主语）和「老鼠」（宾语）│")
print("  │ 的信息——这就叫「融合上下文」                       │")
print("  │                                                    │")
print("  │ 这就是为什么同一个词在不同句子中会有不同的表示：    │")
print("  │ 「bank」在 river bank → 关注 river → 河岸          │")
print("  │ 「bank」在 bank account → 关注 account → 银行      │")
print("  └────────────────────────────────────────────────────┘")

# ═══════════════════════════════════════════════════════════
# 6. 总结
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("📋 回顾：Self-Attention 做了什么")
print("=" * 60)
print("""
  输入：每个词的独立向量（「猫」「追」「老鼠」各自表示）

    ↓

  过程：每个词发出 Query，跟所有词的 Key 比对 → 产生注意力权重

    ↓

  输出：每个词的新向量 = 所有词的 Value 按注意力权重加权求和
        → 新向量里包含了上下文信息！

  ─────────────────────────────────────────────────────────

  一句话总结：

  Self-Attention 让每个词"看到"句子里的其他词，
  从而生成一个融合了上下文的新表示。

  这就是 Transformer 能理解语言的核心秘密。
""")
