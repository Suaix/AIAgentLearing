"""
Step 0 热身：交互式对话循环

运行方式：
    uv run python code/01-foundations/chat_loop.py

功能：
    在终端中与 DeepSeek 连续对话，输入 'quit' 退出
    每次对话会显示 Token 用量统计

学习目标（先不用深入理解，跑起来观察）：
    - 多轮对话如何保持上下文？
    - Token 用量如何随对话增长？
    - 为什么最后会报错？
"""

import os
import sys
from dotenv import load_dotenv

# 如果 openai 未安装，提示安装
try:
    from openai import OpenAI
except ImportError:
    print("❌ 需要安装 openai，请运行：uv add openai")
    sys.exit(1)

# ---- ① 加载环境配置 ----
# .env 文件中的 DEEPSEEK_API_KEY 会被加载为环境变量
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    print("❌ 请在 .env 文件中设置 DEEPSEEK_API_KEY")
    sys.exit(1)

# ---- ② 创建客户端 ----
# base_url 指向 DeepSeek 的 OpenAI 兼容接口
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

# ---- ③ 初始化对话记录 ----
# messages 是 LLM 的"记忆"——它不知道之前说过什么，全靠我们每次把完整对话记录发回去
messages = [
    {"role": "system", "content": "你是一个友好的AI助手，回答尽量简洁。"},
]

# ---- ④ 模型与参数配置 ----
MODEL = "deepseek-v4-flash"  # 快速模型
MAX_TOKENS = 500             # 每次回复最多 500 token

print("=" * 50)
print("🤖  交互式对话循环 (输入 'quit' 退出)")
print(f"📋 模型: {MODEL}")
print(f"📏 每次回复上限: {MAX_TOKENS} token")
print("=" * 50)

# ---- ⑤ 对话循环 ----
total_prompt_tokens = 0
total_completion_tokens = 0
turn = 0

while True:
    # 获取用户输入
    user_input = input(f"\n🧑 你: ")
    if user_input.lower() == "quit":
        break

    turn += 1
    # 将用户消息加入对话记录
    messages.append({"role": "user", "content": user_input})

    # 调用 API
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
    )

    # 提取回复
    assistant_reply = response.choices[0].message.content

    # 提取 Token 用量
    usage = response.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    total_prompt_tokens += prompt_tokens
    total_completion_tokens += completion_tokens

    # 将 AI 回复加入对话记录（关键！下一轮需要它）
    messages.append({"role": "assistant", "content": assistant_reply})

    # 显示结果
    print(f"🤖 AI: {assistant_reply}")
    print(f"   📊 [第{turn}轮] prompt={prompt_tokens} | completion={completion_tokens} | "
          f"累计={total_prompt_tokens + total_completion_tokens} token")

    # 警告：当消息积累到一定程度，可能超出模型上下文窗口
    if len(messages) > 15:
        print(f"   ⚠️  消息数已达 {len(messages)} 条，继续对话可能超出上下文限制！")

print(f"\n📊 总消耗: {total_prompt_tokens + total_completion_tokens} token")
print("👋 再见！")
