import os
import time
import requests
import openai
from memory import remember, recall

class LLMManager:
    def __init__(self, mode="local", local_model="mistral", cloud_model="gpt-4o", groq_model="llama3-8b-8192", openai_api_key=None, groq_api_key=None):
        self.mode = recall("llm_mode") or mode
        self.local_model = local_model
        self.cloud_model = cloud_model
        self.groq_model = groq_model
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    def set_mode(self, mode):
        self.mode = mode
        remember("llm_mode", mode)

    def ask(self, prompt):
        start = time.time()
        response = "[ERROR] Geen respons"
        try:
            if self.mode == "local":
                response = self._ask_ollama(prompt)
            elif self.mode == "openai":
                try:
                    response = self._ask_openai(prompt)
                except Exception as e:
                    print(f"[LLM] Fallback: OpenAI faalde → lokaal: {e}")
                    self.set_mode("local")
                    remember("llm_last_error", f"OpenAI-fout: {e}")
                    response = self._ask_ollama(prompt)
            elif self.mode == "groq":
                try:
                    response = self._ask_groq(prompt)
                except Exception as e:
                    print(f"[LLM] Fallback: Groq faalde → lokaal: {e}")
                    self.set_mode("local")
                    remember("llm_last_error", f"Groq-fout: {e}")
                    response = self._ask_ollama(prompt)
            else:
                return "[INTERNAL_ERROR] Ongeldige modus"
        except Exception as e:
            return f"[INTERNAL_ERROR] {e}"

        duration = time.time() - start
        print(f"[LLM] ({self.mode}) responsduur: {round(duration, 2)} sec")
        return response

    def _ask_ollama(self, prompt):
        url = "http://localhost:11434/api/generate"
        response = requests.post(url, json={"model": self.local_model, "prompt": prompt})
        response.raise_for_status()
        return response.json().get("response", "").strip()

    def _ask_openai(self, prompt):
        if not self.openai_client:
            raise RuntimeError("Geen geldige OpenAI API key")
        r = self.openai_client.chat.completions.create(
            model=self.cloud_model,
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content.strip()

    def _ask_groq(self, prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()