"""
OpenAI-compatible LLM Provider.
"""
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from src.providers.base import BaseLLMProvider

class OpenAICompatibleProvider(BaseLLMProvider):
    """Integrates with OpenAI or any OpenAI-compatible API."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_openai_api_key_here")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "text": "OpenAI API key is missing or not configured.",
                "model": self.model_name,
                "token_usage": {},
                "is_refusal": False,
                "error": "Missing API key"
            }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1)
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                choice = result["choices"][0]["message"]
                usage = result.get("usage", {})
                return {
                    "text": choice.get("content", ""),
                    "model": self.model_name,
                    "token_usage": {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    },
                    "is_refusal": False,
                    "error": None
                }
        except Exception as e:
            return {
                "text": f"Error calling OpenAI API: {e}",
                "model": self.model_name,
                "token_usage": {},
                "is_refusal": False,
                "error": str(e)
            }
