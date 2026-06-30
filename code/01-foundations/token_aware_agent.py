import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url=os.environ.get("DEEPSEEK_BASE_URL"))
system_prompt = {"role": "system", "content": "You are a helpful assistant."}
messages = [system_prompt]

def chat_loop():
    temperature = 0.7
    cost_tokens = 0
    cost_money = 0.0
    current_model="deepseek-v4-flash"
    model_prices = {
        "deepseek-v4-flash": {"input": 0.14, "output": 0.28},
        "deepseek-v4-pro": {"input": 0.435, "output": 0.87}
        }

    while True:
        user_input = input("你:")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat...")
            break

        if user_input.lower() == "/creative":
            temperature = 0.9
            print(f"💡 已切换到创意模式(temperature={temperature})")

        elif user_input.lower() == "/precise":
            temperature = 0.1
            print(f"💡 已切换到精确模式(temperature={temperature})")

        else:
            messages.append({"role": "user", "content": user_input})
            response = client.chat.completions.create(
                model=current_model,
                messages=messages,
                temperature=temperature,
                max_tokens=1000,
            )
            ai_reply_content = response.choices[0].message.content
            print(f"AI: {ai_reply_content}")
            messages.append({"role": "assistant", "content": ai_reply_content})
            cost_tokens += response.usage.total_tokens
            cost_money += response.usage.prompt_tokens * model_prices[current_model]["input"] / 1_000_000 + response.usage.completion_tokens * model_prices[current_model]["output"] / 1_000_000
            print(f"[本轮：{response.usage.total_tokens} tokens | 累计：{cost_tokens} tokens | 费用：${cost_money:.4f}]")
            if len(messages) >= 100:
                print("⚠️ 消息过多，已清理部分历史记录以节省token。")
                messages.pop(1)
                messages.pop(1)


if __name__ == "__main__":
    chat_loop()
