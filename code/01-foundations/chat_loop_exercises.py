"""
Step 3 引导式修改练习

在 chat_loop.py 基础上完成 4 个渐进任务。
每个任务的目标和预期输出都已标注。

用法：
    uv run python code/01-foundations/chat_loop_exercises.py
"""

import os
import sys
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    print("❌ 需要安装 openai，请运行：uv add openai")
    sys.exit(1)

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    print("❌ 请在 .env 文件中设置 DEEPSEEK_API_KEY")
    sys.exit(1)

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
MODEL = "deepseek-v4-flash"

# ============================================================
# 练习 1：改参数 — 从 Flash 换到 Pro 推理模型
# ============================================================
# 任务：把 MODEL 改成 "deepseek-v4-pro"（推理模型），观察差异
# 提示：
#   1. 推理模型会先内部思考（reasoning），再给出回答
#   2. 你需要把 max_tokens 调大（建议 2000），否则 reasoning 消耗 quota 后回答被截断
#   3. 代码骨架已写好，你只需要填入 MODEL 和调整 max_tokens
# 预期输出：你会看到模型在给出回答前有 reasoning_content（内部推理过程）

def exercise1():
    """练习1：切换到推理模型，观察推理过程"""
    print("\n" + "=" * 50)
    print("练习 1：推理模型 vs 普通模型")
    print("=" * 50)

    # TODO: 把 MODEL 改成 "deepseek-v4-pro"
    model = "deepseek-v4-pro"

    # TODO: 把 max_tokens 改大（建议 2000）
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "如果所有的猫都会飞，而 Tom 是一只猫，那么 Tom 会飞吗？请逐步分析。"}
        ],
        max_tokens=2000,
    )

    # 尝试获取推理内容（推理模型特有字段）
    reasoning = getattr(response.choices[0].message, "reasoning_content", None)
    if reasoning:
        print(f"🧠 推理过程: {reasoning[:200]}...")
    else:
        print("⚠️  该模型没有返回 reasoning_content")

    print(f"💬 最终回答: {response.choices[0].message.content}")
    print(f"📊 prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")


# ============================================================
# 练习 2：加功能 — 限制对话轮数自动退出
# ============================================================
# 任务：给对话循环添加"最大轮数限制"，达到上限自动退出
# 提示：
#   1. 在 while True 循环中添加一个计数器检查
#   2. 达到上限时打印提示并 break
#   3. 代码骨架：if ___ >= ___ : break
# 预期输出：输入 3 句话后自动退出

def exercise2():
    """练习2：添加最大轮数限制"""
    print("\n" + "=" * 50)
    print("练习 2：限制轮数自动退出")
    print("=" * 50)

    messages = [
        {"role": "system", "content": "回答简洁，不超过20个字。"},
    ]
    MAX_TURNS = 3  # 最多 3 轮
    # TODO: turn 计数器初始值
    turn = 0

    while True:
        user_input = input(f"\n🧑 你: ")
        if user_input.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_input})
        response = client.chat.completions.create(
            model=MODEL, messages=messages, max_tokens=200
        )
        assistant_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_reply})

        print(f"🤖 AI: {assistant_reply}")
        # TODO: turn 自增
        turn += 1
        # TODO: 检查是否达到 MAX_TURNS，达到则打印提示并 break
        if turn >= MAX_TURNS:
            print(f"⚠️  已达到最大轮数 {MAX_TURNS}，对话结束。")
            break

    print("👋 对话结束")


# ============================================================
# 练习 3：修 Bug — Token 溢出
# ============================================================
# 问题：下面这段代码有 bug，当对话太多时会报错
# 原因：messages 无限制增长，超出模型上下文窗口
# 任务：添加"消息裁剪"逻辑 —— 当消息数超过阈值时，保留 system prompt，
#       删除最老的一组 user+assistant 对话（system message 不能删）
# 提示：
#   1. 先判断 len(messages) 是否超过阈值
#   2. 使用 messages.pop(1) 删除第1条（index=0 是 system prompt，不能删）
#      pop(1) 删除一条后，原来的 index=2 变成 index=1，再 pop(1) 即可
# 预期输出：对话可以无限继续，不会因上下文超长报错

def exercise3():
    """练习3：添加消息裁剪逻辑，防止上下文溢出"""
    print("\n" + "=" * 50)
    print("练习 3：消息裁剪（滑动窗口）")
    print("=" * 50)

    messages = [
        {"role": "system", "content": "回答尽可能简短，不超过15个字。"},
    ]
    MAX_MESSAGES = 7  # 包括 system message，最多保留 7 条消息

    while True:
        user_input = input(f"\n🧑 你: ")
        if user_input.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_input})
        response = client.chat.completions.create(
            model=MODEL, messages=messages, max_tokens=100
        )
        assistant_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_reply})

        print(f"🤖 AI: {assistant_reply}")
        print(f"   📊 消息数={len(messages)}, prompt_tokens={response.usage.prompt_tokens}")

        # TODO: 当 messages 数量 > MAX_MESSAGES 时，裁剪最老的非 system 消息
        # 提示：while len(messages) > MAX_MESSAGES: messages.pop(1)
        # （pop(1) 删除 index=1 的消息，即最老的 user/assistant 消息）
        #
        # TODO: 在这里写你的裁剪代码
        while len(messages) > MAX_MESSAGES:
            messages.pop(1)

    print("👋 对话结束")


# ============================================================
# 练习 4：扩展场景 — 多轮问答记忆验证
# ============================================================
# 任务：写一个"问答记忆测试"——让 AI 先记住三个事实，然后提问验证
# 不要求交互，直接程序化发送多轮消息并验证
# 提示：
#   1. 用代码（不用 input）发送 3 条用户消息，每条告诉 AI 一个事实
#   2. 每条 AI 回复后追加到 messages
#   3. 最后发一条问题验证 AI 是否记住了
#   4. 如果 AI 回答正确，打印 ✅，否则打印 ❌
# 预期输出：
#   事实1: 我的名字是小明  → AI 确认
#   事实2: 我住在北京      → AI 确认
#   事实3: 我喜欢编程      → AI 确认
#   验证问题: 我叫什么名字？住在哪？喜欢什么？
#   ✅ AI 记住了所有三个事实

def exercise4():
    """练习4：多轮记忆验证"""
    print("\n" + "=" * 50)
    print("练习 4：记忆验证测试")
    print("=" * 50)

    messages = [
        {"role": "system", "content": "你是一个记忆力测试助手。记住用户告诉你的每一条信息。回答简洁。"},
    ]

    facts = [
        "我的名字是小明",
        "我住在北京",
        "我喜欢编程",
    ]

    # TODO: 依次发送每个事实，并将 AI 回复追加到 messages
    for fact in facts:
        # 1. 把 fact 作为 user message 加入 messages
        # 2. 调用 API
        # 3. 把 assistant 回复加入 messages
        # 4. 打印 "📝 {fact} → AI: {回复}"
        messages.append({"role": "user", "content": fact})
        response = client.chat.completions.create(
            model=MODEL, messages=messages, max_tokens=500
        )
        assistant_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_reply})
        print(f"📝 {fact} → AI: {assistant_reply}")

    # TODO: 发送验证问题
    question = "请根据你记住的信息回答：我叫什么名字？住在哪个城市？喜欢什么？"
    # 1. 把 question 加入 messages
    # 2. 调用 API
    # 3. 打印 AI 的完整回答
    # 4. 检查回答中是否包含 "小明"、"北京"、"编程"，全部包含打印 ✅，否则 ❌
    messages.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model=MODEL, messages=messages, max_tokens=500
    )
    ai_reply = response.choices[0].message.content
    print(f"🤖 AI: {ai_reply}")
    if "小明" in ai_reply and "北京" in ai_reply and "编程" in ai_reply:
        print("✅ AI 记住了所有三个事实")
    else:
        print("❌ AI 没有记住所有三个事实")

# ============================================================
# 主入口：选择要运行的练习
# ============================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("请选择练习: 1/2/3/4")
        print("用法: uv run python code/01-foundations/chat_loop_exercises.py <编号>")
        sys.exit(1)

    choice = sys.argv[1]
    exercises = {
        "1": exercise1,
        "2": exercise2,
        "3": exercise3,
        "4": exercise4,
    }

    if choice in exercises:
        exercises[choice]()
    else:
        print(f"无效选择: {choice}，请输入 1-4")
