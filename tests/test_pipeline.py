"""
Unit and integration tests for core RAG pipeline.
"""
import pytest
from src.core.pipeline import TripRAGPipeline
from src.providers.mock import DeterministicMockProvider
from src.retrieval.store import TripKnowledgeStore
from src.core.config import config

def test_pipeline_normal_query():
    provider = DeterministicMockProvider()
    store = TripKnowledgeStore(config.csv_path)
    pipeline = TripRAGPipeline(provider=provider, store=store, retriever_k=4)

    response = pipeline.run("What time is my flight to Dubai on 20 Nov?")
    assert response.status == "SUCCESS"
    assert "EK565" in response.answer
    assert len(response.sources) > 0
    assert response.trace_id is not None
    assert response.latency_ms >= 0.0

def test_pipeline_out_of_scope_refusal():
    provider = DeterministicMockProvider()
    store = TripKnowledgeStore(config.csv_path)
    pipeline = TripRAGPipeline(provider=provider, store=store)

    response = pipeline.run("Book me a flight to Paris next week")
    assert response.is_refusal or response.status == "REFUSAL"
    assert "Dubai" in response.answer

def test_pipeline_multi_document_retrieval():
    provider = DeterministicMockProvider()
    store = TripKnowledgeStore(config.csv_path)
    pipeline = TripRAGPipeline(provider=provider, store=store, retriever_k=4)

    response = pipeline.run("Tell me about my entire trip")
    assert len(response.sources) == 4
