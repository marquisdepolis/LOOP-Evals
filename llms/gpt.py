from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
from utils.retry import retry_except
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call(input, GPT):
    client = OpenAI()
    client.api_key = os.getenv('OPENAI_API_KEY')

    response = client.chat.completions.create(
        model=GPT,
        messages=[
            {"role": "system", "content": """You are an AI designed to solve word puzzles. You are brilliant and clever."""},
            {"role": "user", "content": f"{input}"}
        ],
        # response_format={ "type": "json_object" }
    )
    return response.choices[0].message.content