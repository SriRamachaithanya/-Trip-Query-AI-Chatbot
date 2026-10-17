"""
Ollama LLM Provider with connection resilience and timeout handling.
"""
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from src.providers.base import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    """Integrates with a local or remote Ollama server."""

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3.2", timeout_sec: int = 30):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_sec = timeout_sec

    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", headers={"User-Agent": "TripQueryAI"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.1)
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                result = json.loads(response.read().decode("utf-8"))
                response_text = result.get("response", "")
                
                # Approximate token usage if Ollama provides eval_count
                prompt_tokens = result.get("prompt_eval_count", len(prompt.split()))
                completion_tokens = result.get("eval_count", len(response_text.split()))

                return {
                    "text": response_text,
                    "model": self.model_name,
                    "token_usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    },
                    "is_refusal": "cannot assist" in response_text.lower() or "out of scope" in response_text.lower(),
                    "error": None
                }
        except urllib.error.URLError as e:
            return {
                "text": f"Error: Unable to connect to Ollama server at {self.base_url}. Ensure Ollama is running.",
                "model": self.model_name,
                "token_usage": {},
                "is_refusal": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "text": f"Error during generation: {e}",
                "model": self.model_name,
                "token_usage": {},
                "is_refusal": False,
                "error": str(e)
            }
