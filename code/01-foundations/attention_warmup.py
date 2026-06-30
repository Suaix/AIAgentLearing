"""
Step 0 热身：Transformer Self-Attention 直观演示
================================================
不需要 API Key，纯 NumPy 实现。
目标：亲眼看到 Self-Attention 内部每一步的计算过程和中间结果。

核心问题：每个 token 如何"注意"到其他 token？
答案：Query（我想找什么）× Key（我有什么标签）× Value（我的实际内容）
"""

import numpy as np

# 设置随机种子，确保每次运行结果一致
np.random.seed(42)

print("=" * 65)
print("🧠 Transformer Self-Attention 内部演示")
print("=" * 65)

# ═══════════════════════════════════════════════════════════
# 第 1 步：准备输入 — 3 个 token 的 embedding
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("第 1 步：输入 Embedding（3 个 token，每个 4 维向量）")
print("─" * 65)
print("类比：每个 token 是一个「词」的向量表示")
print("我们模拟句子：「我 喜欢 编程」")

# 模拟 3 个 token 的 embedding，每个是 4 维向量
# 在实际 Transformer 中，embedding 维度通常是 512 或 768
X = np.array([
    [1.0, 0.5, 0.2, 0.8],   # token_0: "我"
    [0.3, 0.9, 0.1, 0.4],   # token_1: "喜欢"
    [0.7, 0.2, 0.6, 0.3],   # token_2: "编程"
])

tokens = ["我", "喜欢", "编程"]
for i, (token, vec) in enumerate(zip(tokens, X)):
    print(f"  Token[{i}] \"{token}\" → {vec}")

print(f"\n  输入形状: {X.shape}  ← (seq_len=3, d_model=4)")

# ═══════════════════════════════════════════════════════════
# 第 2 步：定义 Q、K、V 权重矩阵
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("第 2 步：定义 Q、K、V 权重矩阵")
print("─" * 65)
print("Q（Query）：「我想找什么」— 每个 token 发起的「查询」")
print("K（Key）  ：「我是什么」— 每个 token 的「标签」")
print("V（Value）：「我的内容」— 每个 token 的「实际信息」")
print()
print("这 3 个矩阵是从输入 X 通过不同的权重矩阵变换而来：")
print("  Q = X · W_Q,   K = X · W_K,   V = X · W_V")

# 权重矩阵：d_model=4 → d_k=3（为展示方便，缩小维度）
d_k = 3
W_Q = np.random.randn(4, d_k) * 0.5
W_K = np.random.randn(4, d_k) * 0.5
W_V = np.random.randn(4, d_k) * 0.5

print(f"\n  W_Q 形状: {W_Q.shape}  ← (d_model=4, d_k=3)")
print(f"  W_K 形状: {W_K.shape}")
print(f"  W_V 形状: {W_V.shape}")

# ═══════════════════════════════════════════════════════════
# 第 3 步：计算 Q、K、V
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("第 3 步：计算 Q、K、V 矩阵")
print("─" * 65)

Q = X @ W_Q  # (3, 4) × (4, 3) = (3, 3)
K = X @ W_K  # (3, 4) × (4, 3) = (3, 3)
V = X @ W_V  # (3, 4) × (4, 3) = (3, 3)

print(f"  Q 形状: {Q.shape}  ← 每个 token 的「查询」向量")
print(f"  K 形状: {K.shape}  ← 每个 token 的「键」向量")
print(f"  V 形状: {V.shape}  ← 每个 token 的「值」向量")
print()
for i, token in enumerate(tokens):
    print(f"  Token[{i}] \"{token}\"")
    print(f"    Q{i}: {np.round(Q[i], 3)}")
    print(f"    K{i}: {np.round(K[i], 3)}")
    print(f"    V{i}: {np.round(V[i], 3)}")

# ═══════════════════════════════════════════════════════════
# 第 4 步：计算 Attention 分数（Q × K^T）
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("第 4 步：计算 Attention 分数 — Score = Q × K^T")
print("─" * 65)
print("核心操作：每个 token 的 Query 与所有 token 的 Key 做点积")
print("点积结果越大 → 两个 token 越「相关」")
print()

# Q @ K^T: (3, 3) × (3, 3) = (3, 3)
# scores[i][j] = token_i 对 token_j 的注意力原始分数
scores = Q @ K.T

# 缩放：除以 sqrt(d_k)，防止点积过大导致 softmax 梯度消失
scaled_scores = scores / np.sqrt(d_k)

print(f"  原始分数矩阵 (Q×K^T):")
print(f"          \"我\"     \"喜欢\"   \"编程\"")
for i, token_i in enumerate(tokens):
    row = "  ".join(f"{scaled_scores[i][j]:8.3f}" for j in range(len(tokens)))
    print(f"  \"{token_i}\" → [{row}]")

print(f"\n  📐 缩放因子 1/√d_k = 1/√{d_k} = {1/np.sqrt(d_k):.4f}")
print(f"  💡 缩放目的：防止大维度下点积值过大，保持 softmax 梯度")

# ═══════════════════════════════════════════════════════════
# 第 5 步：Softmax — 把分数变成"注意力权重"
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("第 5 步：Softmax — 分数 → 概率分布（注意力权重）")
print("─" * 65)
print("对每一行做 softmax，让每个 token 的注意力权重之和 = 1")
print()

def softmax(x):
    """对矩阵每一行做 softmax"""
    exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))  # 减去最大值防止溢出
    return exp_x / np.sum(exp_x, axis=1, keepdims=True)

attention_weights = softmax(scaled_scores)

print(f"  注意力权重矩阵（每行求和 = 1.0）：")
print(f"            \"我\"       \"喜欢\"     \"编程\"      Σ")
for i, token_i in enumerate(tokens):
    row = "  ".join(f"{attention_weights[i][j]:8.3f}" for j in range(len(tokens)))
    row_sum = np.sum(attention_weights[i])
    print(f"  \"{token_i}\" → [{row}]  {row_sum:.1f}")

print(f"\n  📖 解读示例：")
print(f"  Token「我」的注意力分布：")
for j, token_j in enumerate(tokens):
    bar = "█" * int(attention_weights[0][j] * 50)
    print(f"    对「{token_j}」: {attention_weights[0][j]:.3f} {bar}")

# ═══════════════════════════════════════════════════════════
# 第 6 步：加权求和 — 用注意力权重 重新组合 Value
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("第 6 步：加权求和 — Output = Attention × V")
print("─" * 65)
print("每个 token 的输出 = 它关注的所有 token 的 Value 的加权和")
print()

output = attention_weights @ V  # (3, 3) × (3, 3) = (3, 3)

print(f"  输出矩阵 (形状: {output.shape}):")
print()
for i, token_i in enumerate(tokens):
    print(f"  Token[{i}] \"{token_i}\" 的输出向量:")
    print(f"    = {attention_weights[i][0]:.3f} × V_0 + "
          f"{attention_weights[i][1]:.3f} × V_1 + "
          f"{attention_weights[i][2]:.3f} × V_2")
    print(f"    = {np.round(output[i], 3)}")

# ═══════════════════════════════════════════════════════════
# 第 7 步：可视化 — 看 Attention 做了什么
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("第 7 步：注意力热力图（直观感受 Attention Pattern）")
print("─" * 65)
print()
print("         关注对象 →")
print("         " + "    ".join(f"{t:^10}" for t in tokens))
for i, token_i in enumerate(tokens):
    cells = "  ".join(f"{attention_weights[i][j]:.3f}      " for j in range(len(tokens)))
    print(f"  {token_i}  |  {cells}")
print("  ↓")
print("  查询者")

# 也可以看箭头的粗细表示
print(f"\n  📊 注意力流向（阈值 > 0.25 标出）：")
for i, token_i in enumerate(tokens):
    for j, token_j in enumerate(tokens):
        w = attention_weights[i][j]
        if w > 0.25:
            arrow_len = int(w * 20)
            print(f"  「{token_i}」──{'─' * arrow_len}>({w:.3f})──>「{token_j}」")

# ═══════════════════════════════════════════════════════════
# 总结
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("✅ Self-Attention 完整数据流回顾")
print("=" * 65)
print("""
  X (输入 embedding)          形状: (seq_len, d_model)
  │
  ├─→ Q = X·W_Q  ──────────  形状: (seq_len, d_k)  「我要找什么」
  ├─→ K = X·W_K  ──────────  形状: (seq_len, d_k)  「我有什么标签」
  ├─→ V = X·W_V  ──────────  形状: (seq_len, d_k)  「我的实际内容」
  │
  ├─→ Scores = Q·K^T / √d_k   形状: (seq_len, seq_len)
  │     │                      每个位置 = 一个 token 对另一个 token 的关注度
  │     │
  ├─→ Attention = softmax(Scores)
  │     │                      每行变成概率分布（∑=1）
  │     │
  └─→ Output = Attention · V  形状: (seq_len, d_k)
                                每个 token 的新表示 = 所有 token 的 V 的加权和

  关键洞察：
  ┌─────────────────────────────────────────────────────┐
  │ Self-Attention 让每个 token "看到" 其他 token      │
  │ 输出不再是孤立的词向量，而是融合了上下文的表示      │
  │ 这就是为什么 LLM 能理解 "bank" 在                  │
  │ "river bank" vs "bank account" 中的不同含义        │
  └─────────────────────────────────────────────────────┘
""")

print("👉 接下来思考：如果有多组不同的 Q/K/V 权重（多头注意力），")
print("   模型就能同时学到多种「关注模式」——语法、语义、位置关系等。")
print()
print("运行完成！你已经看到了 Self-Attention 的完整内部计算过程。🎉")
