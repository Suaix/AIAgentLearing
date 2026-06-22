"""
Module 1, Session 1 — LLM 核心概念演示
覆盖：Temperature, Top-P, Streaming, System Prompt, Token 计量
"""
import os
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


def demo_temperature():
    """
    演示 Temperature 参数的效果

    Temperature 控制输出的随机性：
    - 0.0 → 完全确定性（适合数学、代码、事实问答）
    - 1.0 → 较有创意（适合写作、头脑风暴）
    - >1.0 → 非常随机（很少使用）

    本质：在每一步选择下一个 token 时，temperature 调整概率分布。
    低 temperature → 高概率 token 被放大，低概率被压制 → 更确定
    高 temperature → 概率分布被"压平" → 更多样化
    """
    print("\n" + "=" * 60)
    print("🧪 Temperature 对比实验")
    print("=" * 60)

    prompt = "用一句话描述春天的感觉。"

    for temp in [0.0, 0.7, 1.5]:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=300,
        )
        content = response.choices[0].message.content
        reasoning = response.choices[0].message.reasoning_content or ""
        print(f"\n  Temperature={temp:.1f}: {content}")
        if reasoning:
            print(f"    (内部推理: {len(reasoning)} 字)")


def demo_system_prompt():
    """
    演示 System Prompt 对模型行为的控制

    messages 数组中的三种角色：
    - system: 设定 AI 的行为、角色、规则（最优先）
    - user: 用户的输入
    - assistant: AI 之前的回复（多轮对话时用）
    """
    print("\n" + "=" * 60)
    print("🧪 System Prompt 对比实验")
    print("=" * 60)

    question = "解释什么是递归。"

    # 无 system prompt
    r1 = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": question}],
        max_tokens=500,
    )

    # 设定专业角色
    r2 = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": "你是一个教5岁小朋友的老师，用最简单的话解释概念。"},
            {"role": "user", "content": question},
        ],
        max_tokens=500,
    )

    print(f"\n  无 System Prompt:\n    {r1.choices[0].message.content}")
    print(f"\n  有 System Prompt（5岁小朋友老师）:\n    {r2.choices[0].message.content}")


def demo_streaming():
    """
    演示流式输出（Server-Sent Events）

    非流式：等待模型生成完毕，一次性返回
    流式：模型每生成若干字符就返回一个 chunk
         → 用户体验更好（逐字显示）
         → Agent 开发中常用于实时反馈
    """
    print("\n" + "=" * 60)
    print("🧪 流式输出演示")
    print("=" * 60)

    stream = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "用50字介绍机器学习。"}],
        stream=True,
        max_tokens=500,
    )

    print("\n  流式输出: ", end="", flush=True)
    collected_content = []
    collected_reasoning = []
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            collected_content.append(delta.content)
        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
            collected_reasoning.append(delta.reasoning_content)
    content_text = ''.join(collected_content)
    if collected_reasoning:
        print(f"\n  (内部推理: {len(''.join(collected_reasoning))} 字)")
    print(f"\n  最终输出: {len(content_text)} 字")


def demo_token_counting():
    """
    演示 Token 计量

    Token 是 LLM 处理文本的基本单位，不是字符也不是单词。
    - 英文：约 1 token ≈ 0.75 个单词
    - 中文：约 1 token ≈ 0.5 个汉字（中文 tokenize 效率低于英文）

    计费按 token 总量算：
    总费用 = 输入 tokens × 输入单价 + 输出 tokens × 输出单价

    以 deepseek-v4-flash 为例（[待查证当前定价]）：
    - 输入：约 ¥1/百万 tokens
    - 输出：约 ¥2/百万 tokens
    """
    print("\n" + "=" * 60)
    print("🧪 Token 计量演示")
    print("=" * 60)

    texts = [
        ("英文短句", "Hello, how are you?"),
        ("中文短句", "你好，你今天怎么样？"),
        ("英文段落", "Artificial Intelligence is a branch of computer science "
         "that aims to create intelligent machines that can perform tasks "
         "that typically require human intelligence."),
        ("中文段落", "人工智能是计算机科学的一个分支，旨在创造能够执行通常需要"
         "人类智能才能完成的任务的智能机器。"),
    ]

    for label, text in texts:
        # 用 tiktoken 或简单估算，这里用 API 返回的实际值
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": text}],
            max_tokens=1,  # 只要 1 个输出 token 即可统计输入
        )
        prompt_tokens = response.usage.prompt_tokens
        chars = len(text)
        print(f"\n  {label}: {chars} 字符 → {prompt_tokens} tokens"
              f"  (约 {chars/prompt_tokens:.1f} 字符/token)")


if __name__ == "__main__":
    demo_temperature()
    demo_system_prompt()
    demo_streaming()
    demo_token_counting()
    print("\n" + "=" * 60)
    print("✅ 核心概念演示完成")
    print("=" * 60)
