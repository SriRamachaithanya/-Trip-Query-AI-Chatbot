"""
Core RAG Pipeline for Trip Query AI Chatbot.
Orchestrates Tracing -> Retrieval -> Prompt Formatting -> Model Generation -> Response Structuring.
"""
import time
from typing import Optional
from src.core.config import config
from src.core.schemas import ChatbotResponse, RetrievedDocument
from src.core.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, format_context_documents
from src.retrieval.store import TripKnowledgeStore
from src.providers import get_provider, BaseLLMProvider
from src.tracing import default_tracer, Tracer

class TripRAGPipeline:
    """Production RAG Pipeline with structured telemetry and provider abstraction."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        store: Optional[TripKnowledgeStore] = None,
        tracer: Optional[Tracer] = None,
        retriever_k: int = 4
    ):
        self.provider = provider or get_provider(
            provider_type=config.llm_provider,
            ollama_base_url=config.ollama_base_url,
            ollama_model=config.ollama_model,
            openai_api_key=config.openai_api_key,
            openai_base_url=config.openai_base_url,
            openai_model=config.openai_model
        )
        self.store = store or TripKnowledgeStore(config.csv_path)
        self.tracer = tracer or default_tracer
        self.retriever_k = retriever_k

    def run(self, query: str) -> ChatbotResponse:
        """Executes full RAG workflow for a query with end-to-end tracing."""
        trace = self.tracer.start_trace(query=query, pipeline_version="2.0.0")
        start_time = time.time()

        try:
            # 1. Retrieval Stage
            with self.tracer.span("retrieval", {"k": self.retriever_k}):
                retrieved_docs = self.store.retrieve(query, k=self.retriever_k)

            # 2. Prompt Construction Stage
            with self.tracer.span("prompt_construction"):
                context_str = format_context_documents(retrieved_docs)
                user_prompt = USER_PROMPT_TEMPLATE.format(context=context_str, question=query)

            # 3. Model Generation Stage
            with self.tracer.span("llm_generation", {"provider": self.provider.__class__.__name__}):
                llm_output = self.provider.generate(
                    prompt=user_prompt,
                    system_prompt=SYSTEM_PROMPT
                )

            total_latency = round((time.time() - start_time) * 1000, 2)
            answer_text = llm_output.get("text", "")
            is_refusal = llm_output.get("is_refusal", False)
            error = llm_output.get("error")

            # Update trace record
            trace.token_usage = llm_output.get("token_usage", {})
            self.tracer.end_trace(status="ERROR" if error else "SUCCESS", error=error)

            return ChatbotResponse(
                query=query,
                answer=answer_text,
                sources=retrieved_docs,
                trace_id=trace.trace_id,
                status="ERROR" if error else ("REFUSAL" if is_refusal else "SUCCESS"),
                error=error,
                latency_ms=total_latency,
                token_usage=llm_output.get("token_usage", {}),
                is_refusal=is_refusal
            )

        except Exception as e:
            total_latency = round((time.time() - start_time) * 1000, 2)
            self.tracer.end_trace(status="ERROR", error=str(e))
            return ChatbotResponse(
                query=query,
                answer=f"An error occurred while processing your request: {e}",
                trace_id=trace.trace_id,
                status="ERROR",
                error=str(e),
                latency_ms=total_latency
            )
