"""
Step 3 引导式修改：操控 Self-Attention
======================================
4 个渐进任务。脚手架已搭好，你只需要填 TODO 部分。
"""

import numpy as np

# ═══════════════════════════════════════════════════════════
# 共享工具函数（脚手架，不用管）
# ═══════════════════════════════════════════════════════════

def softmax(x):
    """安全的 softmax 实现"""
    exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

def print_attention(tokens, attn_weights, title="注意力分布"):
    print(f"\n  {title}：")
    print(f"           ", end="")
    for t in tokens:
        print(f"{t:^10}", end="")
    print("    Σ")
    for i, t_i in enumerate(tokens):
        row_sum = np.sum(attn_weights[i])
        print(f"  {t_i:^6}  ", end="")
        for j in range(len(tokens)):
            print(f"{attn_weights[i][j]:^10.3f}", end="")
        print(f"  {row_sum:.1f}")

# 手工设计的 embeddings 和权重（来自 Step 0 warmup，不用管）
embeddings = {
    "猫":   np.array([1.0, 0.8, 0.1, 0.2, 0.3]),
    "追":   np.array([0.2, 0.3, 0.9, 0.8, 0.2]),
    "老鼠": np.array([0.9, 0.7, 0.1, 0.2, 0.4]),
}
W_Q = np.array([[0.1,0.1,0.5],[0.1,0.1,0.2],[0.8,0.3,0.1],[0.7,0.2,0.1],[0.1,0.8,0.3]])
W_K = np.array([[0.9,0.2,0.1],[0.7,0.1,0.1],[0.1,0.1,0.8],[0.1,0.1,0.7],[0.2,0.9,0.2]])
W_V = np.array([[0.8,0.1,0.1],[0.7,0.1,0.1],[0.1,0.8,0.1],[0.1,0.7,0.1],[0.1,0.1,0.8]])

tokens = ["猫", "追", "老鼠"]
X = np.array([embeddings[t] for t in tokens])
d_k = 3
Q = X @ W_Q
K = X @ W_K
V = X @ W_V

print("=" * 60)
print("🧪 Step 3：引导式修改")
print("=" * 60)

# ═══════════════════════════════════════════════════════════
# 实验 ①：改参数 — 温度系数
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("实验 ① 改参数：Temperature 控制注意力的「锐度」")
print("=" * 60)
print("""
  Attention = softmax( (Q·K^T) / (√d_k × temperature) )

  temperature 越小 → 注意力越集中在一个词上
  temperature 越大 → 注意力越均匀分散

  回忆：这和 LLM API 里的 temperature 参数原理一样！
""")

# ─── TODO ①：补全下面的公式 ───
# 把 3 个不同温度值跑一遍，观察注意力分布如何变化
# 提示：公式是 scaled_scores = scores / (np.sqrt(d_k) * temp)

for temp in [0.1, 1.0, 10.0]:
    scores = Q @ K.T

    # ↓↓↓ TODO：用 temperature 计算 scaled_scores ↓↓↓
    scaled_scores = scores / (np.sqrt(d_k) * temp)   # 👈 改成正确的公式
    # ↑↑↑

    if scaled_scores is not None:
        attn = softmax(scaled_scores)
        print_attention(tokens, attn, f"temperature = {temp}")

# ═══════════════════════════════════════════════════════════
# 实验 ②：加功能 — 第 2 个 Attention Head
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("实验 ② 加功能：实现第 2 个 Attention Head")
print("=" * 60)
print("""
  实际 Transformer 用 Multi-Head：并行跑多组 Q/K/V。
  这里给你第 2 组权重，你需要完成和第 1 组一样的计算步骤。
""")

# Head 2 的权重（已提供，和第 1 组不同，会产生不同的关注模式）
W_Q2 = np.array([[0.8,0.1,0.1],[0.7,0.2,0.1],[0.1,0.8,0.1],[0.1,0.7,0.1],[0.2,0.2,0.9]])
W_K2 = np.array([[0.1,0.8,0.1],[0.1,0.9,0.1],[0.8,0.1,0.1],[0.7,0.1,0.1],[0.1,0.1,0.8]])
W_V2 = np.array([[0.1,0.8,0.1],[0.2,0.7,0.1],[0.8,0.1,0.2],[0.7,0.1,0.2],[0.1,0.2,0.7]])

# ─── TODO ②：用 W_Q2/W_K2/W_V2 计算 Head 2 的注意力 ───
# 提示：和 warmup 里一模一样的步骤：
#   Q2 = X @ W_Q2 → K2 = X @ W_K2 → V2 = X @ W_V2
#   scores2 = Q2 @ K2.T / sqrt(d_k) → attn2 = softmax(scores2)

# TODO: 补全下面 5 行
Q2 = X @ W_Q2    # 👈
K2 = X @ W_K2    # 👈
V2 = X @ W_V2    # 👈
scores2 = Q2 @ K2.T / np.sqrt(d_k)    # 👈
attn2 = softmax(scores2)    # 👈

if attn2 is not None:
    print_attention(tokens, attn2, "Head 2 的注意力分布")

    # Head 1 标准注意力（temperature=1）用于对比
    attn_head1 = softmax(Q @ K.T / np.sqrt(d_k))
    print("\n  📊 两个 Head 对比（每个词最关注谁）：")
    for i, t in enumerate(tokens):
        h1_top = tokens[np.argmax(attn_head1[i])]
        h2_top = tokens[np.argmax(attn2[i])]
        same = "✓ 相同" if h1_top == h2_top else "✗ 不同！"
        print(f"    {t} → Head1:{h1_top}  Head2:{h2_top}  {same}")

# ═══════════════════════════════════════════════════════════
# 实验 ③：修 Bug — 不安全的 Softmax
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("实验 ③ 修 Bug：Softmax 数值溢出")
print("=" * 60)

def unsafe_softmax(x):
    """🐛 BUG：没有减最大值的 softmax"""
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

small_scores = np.array([[1.0, 2.0, 3.0]])
large_scores = np.array([[800.0, 900.0, 1000.0]])  # exp(1000) 远超 float64 上限，必溢出

print("\n  小数值 [1, 2, 3]：")
print(f"    安全版:   {softmax(small_scores)[0]}")
print(f"    不安全版: {unsafe_softmax(small_scores)[0]}")

# ─── TODO ③：测试大数值，观察 unsafe_softmax 的 bug ───
# 先预测：unsafe_softmax(large_scores) 会出什么问题？
# 然后取消注释下面这行，运行验证你的预测：
print("\n  大数值 [800, 900, 1000]：")
print(f"    安全版:   {softmax(large_scores)[0]}")
print(f"    不安全版: {unsafe_softmax(large_scores)[0]}")  # ← 取消注释这行

# ═══════════════════════════════════════════════════════════
# 实验 ④：扩展场景 — 新句子「学生 读 书」
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("实验 ④ 扩展场景：新句子「学生 读 书」")
print("=" * 60)
print("""
  任务：为新句子设计 embedding，然后计算注意力。
  提示：参考 warmup 的设计思路——
    「学生」和「书」是名词 → 动物性/名词性维度应该高
    「读」是动词 → 动作性维度应该高
""")

# ─── TODO ④：设计 3 个词的 embedding（每个 5 维）───
# 5 个维度分别代表：[动物性/名词性, 大小, 动作性, 力度, 情感]

new_embeddings = {
    "学生": np.array([0.9, 0.1, 0.1, 0.1, 0.1]),   # 👈 名词，名词性高
    "读":   np.array([0.1, 0.1, 0.9, 0.1, 0.1]),   # 👈 动词，动作性高
    "书":   np.array([0.9, 0.1, 0.1, 0.1, 0.1]),   # 👈 名词，名词性高
}

# ─── 用已有的 W_Q/W_K/W_V 计算注意力（下面几行补全）───
new_tokens = ["学生", "读", "书"]

# TODO: 构建输入矩阵 new_X（3行 × 5列）
new_X = np.array([new_embeddings[t] for t in new_tokens])  # 👈 补全

# TODO: 计算 new_Q, new_K, new_V
new_Q = new_X @ W_Q  # 👈 补全
new_K = new_X @ W_K  # 👈 补全
new_V = new_X @ W_V  # 👈 补全

# TODO: 计算注意力权重
new_scores = new_Q @ new_K.T / np.sqrt(d_k)  # 👈 补全
new_attn = softmax(new_scores)  # 👈 补全

# 取消下面的注释来运行：
print_attention(new_tokens, new_attn, "「学生 读 书」注意力分布")

print("\n" + "=" * 60)
print("🏁 实验文件已就绪，请逐个完成 TODO 后运行。")
print("=" * 60)
print("运行方式：python3 code/01-foundations/attention_step3.py")
