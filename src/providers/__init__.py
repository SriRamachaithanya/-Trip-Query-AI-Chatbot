from src.providers.base import BaseLLMProvider
from src.providers.mock import DeterministicMockProvider
from src.providers.ollama import OllamaProvider
from src.providers.openai import OpenAICompatibleProvider

def get_provider(provider_type: str = "mock", **kwargs) -> BaseLLMProvider:
    """Factory function to instantiate the requested provider."""
    p = provider_type.lower()
    if p == "ollama":
        return OllamaProvider(
            base_url=kwargs.get("ollama_base_url", "http://localhost:11434"),
            model_name=kwargs.get("ollama_model", "llama3.2")
        )
    elif p == "openai":
        return OpenAICompatibleProvider(
            api_key=kwargs.get("openai_api_key", ""),
            base_url=kwargs.get("openai_base_url", "https://api.openai.com/v1"),
            model_name=kwargs.get("openai_model", "gpt-4o-mini")
        )
    else:
        return DeterministicMockProvider()

__all__ = [
    "BaseLLMProvider",
    "DeterministicMockProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "get_provider"
]
