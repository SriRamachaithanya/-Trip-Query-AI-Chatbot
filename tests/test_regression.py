"""
Regression Test Suite for Trip Query AI Chatbot.
Derived from real historical failure modes, edge cases, and safety checks.
"""
import pytest
from src.core.pipeline import TripRAGPipeline
from src.providers.mock import DeterministicMockProvider
from src.retrieval.store import TripKnowledgeStore
from src.core.config import config

@pytest.fixture
def pipeline():
    provider = DeterministicMockProvider()
    store = TripKnowledgeStore(config.csv_path)
    return TripRAGPipeline(provider=provider, store=store, retriever_k=4)

def test_regression_flight_ek565_not_confused_with_ek566(pipeline):
    """Ensure outbound flight EK565 is not mixed up with return flight EK566."""
    resp_outbound = pipeline.run("What is my outbound flight to Dubai?")
    assert "EK565" in resp_outbound.answer
    assert "EK566" not in resp_outbound.answer

    resp_return = pipeline.run("What is my return flight to Bangalore?")
    assert "EK566" in resp_return.answer
    assert "EK565" not in resp_return.answer

def test_regression_hotel_checkin_sequence(pipeline):
    """Ensure check-in dates for Address Downtown (Nov 20) and Hilton Jumeirah (Nov 22) are maintained."""
    resp = pipeline.run("Which hotel am I staying at first?")
    assert "Address Downtown" in resp.answer
    assert "Hilton Jumeirah" not in resp.answer

def test_regression_unsupported_budget_confirmation(pipeline):
    """Ensure system never claims entire trip is under $1000 when prices are unrecorded."""
    resp = pipeline.run("Confirm that my entire Dubai itinerary costs under $1000 total including flights.")
    assert any(term in resp.answer.lower() for term in ["cannot confirm", "pricing not available", "not recorded", "does not contain"])

def test_regression_empty_and_whitespace_query(pipeline):
    """Ensure empty or whitespace queries do not crash the pipeline."""
    resp_spaces = pipeline.run("     ")
    assert resp_spaces.status == "SUCCESS"
    assert len(resp_spaces.answer) > 10

    resp_gibberish = pipeline.run("???!!! --- &&&")
    assert resp_gibberish.status == "SUCCESS"
    assert len(resp_gibberish.answer) > 10

def test_regression_out_of_scope_rejection(pipeline):
    """Ensure out-of-scope queries (e.g. Tokyo, Paris) are politely declined."""
    resp_tokyo = pipeline.run("Where is the best ramen in Tokyo?")
    assert resp_tokyo.is_refusal or "Dubai" in resp_tokyo.answer
