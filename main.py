"""
Trip Query AI Chatbot - Interactive Terminal Application.
Production-ready CLI entry point with provider auto-detection,
end-to-end tracing, and multi-document retrieval.
"""
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.core.pipeline import TripRAGPipeline
from src.core.config import config
from src.providers import get_provider

def main():
    print("=" * 60)
    print("🌴 Welcome to the Dubai Trip Query AI Chatbot 🌴")
    print("=" * 60)

    # Detect provider availability
    active_provider = get_provider(
        provider_type=config.llm_provider,
        ollama_base_url=config.ollama_base_url,
        ollama_model=config.ollama_model,
        openai_api_key=config.openai_api_key,
        openai_base_url=config.openai_base_url,
        openai_model=config.openai_model
    )

    if not active_provider.is_available() and config.llm_provider != "mock":
        print(f"[NOTE] Configured provider '{config.llm_provider}' is currently unreachable.")
        print("       Automatically falling back to deterministic offline Mock provider.")
        active_provider = get_provider("mock")

    pipeline = TripRAGPipeline(provider=active_provider, retriever_k=config.retriever_k)
    print(f"Active Provider: {active_provider.__class__.__name__}")
    print("Type your questions about flights, hotels, activities, and timings.")
    print("Type 'q' or 'exit' to quit.\n")

    while True:
        try:
            print("-" * 50)
            question = input("Ask a query about the Dubai Trip: ").strip()
            if not question:
                continue
            if question.lower() in ["q", "quit", "exit"]:
                print("\nGoodbye! Have a great trip to Dubai!")
                break

            response = pipeline.run(question)

            print("\nResponse:")
            print(response.answer)
            print(f"\n[Trace ID: {response.trace_id} | Latency: {response.latency_ms}ms | Sources: {len(response.sources)}]")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break

if __name__ == "__main__":
    main()
