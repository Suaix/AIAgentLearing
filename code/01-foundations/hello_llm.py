"""
Module 1, Session 1 — 第一个 LLM API 调用
使用 DeepSeek API（OpenAI 兼容接口）
"""

import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 中的环境变量
load_dotenv()

# 初始化 DeepSeek 客户端（使用 OpenAI 兼容接口）
# trust_env=False 绕过系统代理设置（直接连接 DeepSeek API）
http_client = httpx.Client(trust_env=False)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),  # https://api.deepseek.com
    http_client=http_client,
)


def simple_chat():
    """最简单的对话调用"""
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": "你是一个有帮助的AI助手。"},
            {"role": "user", "content": "什么是 AI Agent？用一句话解释。"},
        ],
    )

    # 整个 response 对象
    print("=== 完整响应对象 ===")
    print(response)
    print()

    # 只看回复内容
    print("=== 模型回复 ===")
    print(response.choices[0].message.content)
    print()

    # Token 用量
    print("=== Token 用量 ===")
    print(f"  输入 tokens: {response.usage.prompt_tokens}")
    print(f"  输出 tokens: {response.usage.completion_tokens}")
    print(f"  总计 tokens: {response.usage.total_tokens}")


if __name__ == "__main__":
    simple_chat()
