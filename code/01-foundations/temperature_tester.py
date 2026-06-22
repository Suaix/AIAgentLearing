import os

from dotenv import load_dotenv
import httpx
from openai import OpenAI

load_dotenv()

http_client = httpx.Client(trust_env=False)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    http_client=http_client,
)

def test_temperature():
    '''
      任务：写一个 temperature_tester.py，放到 code/01-foundations/ 下，完成以下功能：

        ▎ 用同一个问题（"1+1等于几？请先分析，再给出答案。"），分别以 temperature=0.0 和 temperature=1.5 各调用 3 次。对比 6 次输出的内容和token 消耗，把结果打印成表格。

        要求：
        - 输出必须包含：temperature 值、第几次调用、回复字数、prompt_tokens、completion_tokens、回复内容（截取前 60 字）
        - .env 里的 API Key 你已经有了，直接加载
    '''
    question="1+1等于几？请先分析，再给出答案。"
    temp_value=0.0
    count=0
    
    while(count < 3):
        client.chat.completions.create(
            model="deepseek-v4-flash"
        )
