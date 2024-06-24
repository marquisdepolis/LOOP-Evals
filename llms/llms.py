from groq import Groq
from openai import OpenAI
from anthropic import Anthropic
import os
import json
import time
import requests
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
from utils.retry import retry_except
from tenacity import retry, stop_after_attempt, wait_fixed

system_message = "You are an AI trained to be a brilliant puzzle solver and a genius at lateral thinking. You are brilliant and conscientious."

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_gpt(input, GPT, system_p = system_message, temp = 0.7):
    client = OpenAI()
    client.api_key = os.getenv('OPENAI_API_KEY')

    response = client.chat.completions.create(
        model=GPT,
        messages=[
            {"role": "system", "content": system_p},
            {"role": "user", "content": f"{input}"}
        ]
    )
    return response.choices[0].message.content

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_gpt_assistant(input, INSTRUCTION, GPT, temp = 0.7):
    client = OpenAI()
    client.api_key = os.getenv('OPENAI_API_KEY')

    assistant = client.beta.assistants.create(
    name="PoY Evaluator to read DB",
    instructions=INSTRUCTION,
    model=GPT
    )

    ASSISTANT_ID = assistant.id

    run, thread = submit_message_and_create_run(client, ASSISTANT_ID, input)
    returned_response = wait_on_run_and_get_response(client, run, thread)
    if isinstance(returned_response, list):
        returned_response = ' '.join(map(str, returned_response))

    returned_response = returned_response.replace("\\\\n", "\\n")
    returned_response = returned_response.strip()

    return returned_response

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_gpt_json(input, GPT, system_p = system_message, temp = 0.7):
    client = OpenAI()
    client.api_key = os.getenv('OPENAI_API_KEY')

    response = client.chat.completions.create(
        model=GPT,
        messages=[
            {"role": "system", "content": system_p},
            {"role": "user", "content": f"Respond in JSON. {input}"}
        ],
        response_format={ "type": "json_object" }
    )
    return response.choices[0].message.content

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def llm_call_claude(input, LLM, system_p = system_message, temp = 0.7):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=LLM,
        system = system_p,
        messages=[
            {"role": "user", "content": f"{input}"}
        ],
        temperature=temp,
        max_tokens=4096,
    )
    return response.content[0].text

            #  <examples>
            #  {'answer': 'CARE\nAREA\nRACE\nEARN'}
            #  {'answer': 'CRAB\nAIDE\nLEAN\nMEAN'}
            #  {'answer': 'CARE\nANON\nRIDO\nEDEN'}
            #  {'answer': 'CALM\nARIA\nLAID\nMEAN'}
            #  {'answer': 'CHEER\nOCEAN\nMEANS\nEARTH\nTRAIN'}
            #  {'answer': 'CHAIN\nHEARD\nALONE\nIRONS\nNEEDS'}
            #  </examples>
    
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_claude_json(input, LLM, system_p = system_message, temp = 0.7):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=LLM,
        system = system_p,
        messages=[
            {"role": "user", "content": f"""{input}.
             Give me the answer in JSON."""},
            {"role": "assistant", "content": "Here is the JSON requested:\n{"}
        ],
        temperature=temp,
        max_tokens=4096,
    )
    message = response.content[0].text
    output_json = json.loads("{" + message[:message.rfind("}") + 1])
    return output_json

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_gemini(prompt, model="gemini-1.5-pro", system_p=system_message):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40
    }
    model = genai.GenerativeModel(
        model_name=model,
        generation_config=generation_config,
    )
    response = model.generate_content(prompt)
    return response.text

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_gemini_json(prompt, model="gemini-1.5-pro", schema, system_p=system_message):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "response_mime_type": "application/json"
    }
    model = genai.GenerativeModel(
        model_name=model,
        generation_config=generation_config,
    )
    response = model.generate_content(f"The prompt: {prompt}. Please reply using a JSON schema like this: {schema}")
    return response.text

# @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_ollama_json(prompt, LLM = "llama3:8b", temp = 0.7):
    r = requests.post('http://0.0.0.0:11434/api/generate',
                      json={
                          'model': LLM, #llama2:7b
                          'prompt': f"{prompt}. Return this as JSON.",
                          'format': 'json',
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

    print(full_response)
    return full_response

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_ollama(prompt, LLM = "llama3:8b", temp = 0.7):
    r = requests.post('http://0.0.0.0:11434/api/generate',
                      json={
                          'model': LLM,
                          'prompt': f"{prompt}"
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

    print(full_response)
    return full_response

@retry_except(exceptions_to_catch=(IndexError, ZeroDivisionError), tries=3, delay=2)
def llm_call_groq(prompt, system_p = system_message, model:str="llama3-70b-8192", temp = 0.7):
    system_prompt = system_p
    client = Groq()
    messages = [{
            "role": "system",
            "content": system_prompt
        }, 
        {
            "role": "user",
            "content": prompt
        }]
    response = client.chat.completions.create(messages=messages, model=model, temperature = temp)
    return response.choices[0].message.content

def submit_message_and_create_run(client, assistant_id, prompt):
    """
    Submit the message and create the run
    """
    thread = client.beta.threads.create() # If you replace this globally it appends all answers to the one before.
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)
    return client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id, temperature=0.7), thread

def wait_on_run_and_get_response(client, run, thread):
    """
    Wait on run
    """
    while run.status in ("queued","in_progress"):
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(0.5)
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="asc")
    return [m.content[0].text.value for m in messages if m.role == 'assistant']
