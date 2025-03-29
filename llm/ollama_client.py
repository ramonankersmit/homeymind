# Stuur prompt naar lokaal Ollama model
import requests

def get_response(prompt, config):
    system_prompt = open('prompts/system_prompt.txt').read()
    payload = {
        "model": config['llm']['model'],
        "prompt": f"{system_prompt}\n{prompt}",
        "stream": False
    }
    res = requests.post(config['llm']['endpoint'] + "/api/generate", json=payload)
    return res.json()['response']
