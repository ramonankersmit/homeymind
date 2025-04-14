"""
LLM Manager module for HomeyMind.

This module provides a unified interface for interacting with different Large Language Models (LLMs).
It supports local models through Ollama, cloud models through OpenAI, and Groq models.
The manager can automatically fallback to local models if cloud services are unavailable.
"""

import os
import time
import requests
import openai
from app.core.memory import remember, recall

class LLMManager:
    """
    Manager class for handling LLM interactions.
    
    This class provides a unified interface for interacting with different LLM providers
    and handles automatic fallback to local models when cloud services are unavailable.
    """
    
    def __init__(self, config):
        self.config = config
        self.provider = config['llm']['provider']
        self.local_model = config['llm']['local_model']
        self.cloud_model = config['llm']['cloud_model']
        self.groq_model = config['llm']['groq_model']
        self.http_config = config['llm']['http']
        self.prompt_path = config['llm']['prompt_path']
        self.system_prompt = self._load_system_prompt()
        self.openai_api_key = config['llm'].get('openai_api_key')  # Get from llm section
        self.groq_api_key = config['llm'].get('groq_api_key')      # Get from llm section
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.mode = recall("llm_mode") or self.provider  # Initialize mode from memory or use provider from config

    def _load_system_prompt(self):
        try:
            with open(self.prompt_path, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            print(f"Error: System prompt file not found at {self.prompt_path}")
            return ""

    def set_mode(self, mode):
        """
        Set the LLM mode and remember it for future sessions.
        
        Args:
            mode (str): The mode to set ("local", "openai", or "groq").
        """
        self.mode = mode
        remember("llm_mode", mode)

    def ask(self, prompt):
        """
        Send a prompt to the appropriate LLM based on the current mode.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            
        Returns:
            str: The LLM's response.
            
        Note:
            If the cloud service fails, it will automatically fallback to the local model
            and remember the error for future reference.
        """
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
        """
        Send a prompt to the local Ollama model.
        
        Args:
            prompt (str): The prompt to send.
            
        Returns:
            str: The model's response.
            
        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        url = f"http://{self.http_config['host']}:{self.http_config['port']}{self.http_config['endpoint']}"
        response = requests.post(url, json={"model": self.local_model, "prompt": prompt})
        if response.status_code == 200:
            return response.json()['response']
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    def _ask_openai(self, prompt):
        """
        Send a prompt to the OpenAI model.
        
        Args:
            prompt (str): The prompt to send.
            
        Returns:
            str: The model's response.
            
        Raises:
            RuntimeError: If no valid OpenAI API key is available.
            openai.OpenAIError: If the API request fails.
        """
        if not self.openai_client:
            raise RuntimeError("Geen geldige OpenAI API key")
        r = self.openai_client.chat.completions.create(
            model=self.cloud_model,
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content.strip()

    def _ask_groq(self, prompt):
        """
        Send a prompt to the Groq model.
        
        Args:
            prompt (str): The prompt to send.
            
        Returns:
            str: The model's response.
            
        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
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