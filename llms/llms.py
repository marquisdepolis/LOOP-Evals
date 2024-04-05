from openai import OpenAI
from anthropic import Anthropic
import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()
from utils.retry import retry_except
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_gpt(input, GPT):
    client = OpenAI()
    client.api_key = os.getenv('OPENAI_API_KEY')

    response = client.chat.completions.create(
        model=GPT,
        messages=[
            {"role": "system", "content": """You are an AI designed to solve word puzzles. You are brilliant and clever."""},
            {"role": "user", "content": f"{input}"}
        ]
    )
    return response.choices[0].message.content

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_json(input, GPT):
    client = OpenAI()
    client.api_key = os.getenv('OPENAI_API_KEY')

    response = client.chat.completions.create(
        model=GPT,
        messages=[
            {"role": "system", "content": """You are an AI designed to solve word puzzles. You are brilliant and clever."""},
            {"role": "user", "content": f"Respond in JSON. {input}"}
        ],
        response_format={ "type": "json_object" }
    )
    return response.choices[0].message.content

# @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_claude(input, LLM):
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=LLM,
        messages=[
            {"role": "user", "content": f"{input}"}
        ],
        system="You are an AI designed to solve word puzzles. You are brilliant and clever.",
        max_tokens=4096,
    )
    return response.content[0].text

# @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_ollama(prompt, LLM = "mistral"):
    r = requests.post('http://0.0.0.0:11434/api/generate',
                      json={
                          'model': LLM, #llama2:7b
                          'prompt': f"{prompt}."# Return this as JSON.",
                        #   'format': 'json',
                      },
                      stream=False)
    full_response = ""    
    for line in r.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            json_line = json.loads(decoded_line)
            full_response += json_line.get("response", "")
            if json_line.get("done"):
                break

    # print(full_response)
    return full_response