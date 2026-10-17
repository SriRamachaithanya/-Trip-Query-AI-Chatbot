"""
Unit and integration tests for AI Evaluation Harness.
"""
import pytest
from pathlib import Path
from src.evals.schemas import EvalCase
from src.evals.deterministic import evaluate_deterministic
from src.evals.runner import load_dataset
from src.evals.judge import LLMJudgeEvaluator
from src.core.schemas import ChatbotResponse, RetrievedDocument
from src.providers.mock import DeterministicMockProvider

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def test_dataset_loader_validates_32_cases():
    dataset_path = WORKSPACE_ROOT / "evals" / "datasets" / "v1.jsonl"
    cases = load_dataset(dataset_path)
    assert len(cases) >= 30, f"Expected at least 30 cases, found {len(cases)}"
    
    # Check that required fields are present
    for case in cases:
        assert case.id.startswith("TC-")
        assert case.input
        assert case.expected_behavior
        assert isinstance(case.tags, list)

def test_deterministic_evaluator_passes_valid_response():
    case = EvalCase(
        id="TC-TEST-PASS",
        dataset_version="v1.0",
        difficulty="easy",
        tags=["flights"],
        input="What is my flight to Dubai?",
        expected_behavior="Mentions EK565",
        evaluation_criteria={"required_keywords": ["EK565", "15:30"]}
    )
    response = ChatbotResponse(
        query="What is my flight to Dubai?",
        answer="Your flight is Emirates EK565 departing at 15:30."
    )
    checks = evaluate_deterministic(case, response)
    assert all(c.passed for c in checks)

def test_deterministic_evaluator_identifies_deliberate_failure():
    """Acceptance Criteria: A deliberately failing test is identified correctly."""
    case = EvalCase(
        id="TC-TEST-FAIL",
        dataset_version="v1.0",
        difficulty="easy",
        tags=["flights"],
        input="What is my flight to Dubai?",
        expected_behavior="Mentions EK565",
        evaluation_criteria={"required_keywords": ["EK565", "15:30"]}
    )
    # Flawed response lacking required keyword
    response = ChatbotResponse(
        query="What is my flight to Dubai?",
        answer="You are taking a flight from New York to London on BA100."
    )
    checks = evaluate_deterministic(case, response)
    failed_checks = [c for c in checks if not c.passed]
    assert len(failed_checks) > 0
    assert any(c.check_name == "required_keywords" for c in failed_checks)

def test_deterministic_evaluator_empty_output_detection():
    case = EvalCase(
        id="TC-EMPTY",
        dataset_version="v1.0",
        difficulty="easy",
        tags=["edge_case"],
        input="Hello",
        expected_behavior="Greets user",
        evaluation_criteria={}
    )
    response = ChatbotResponse(query="Hello", answer="")
    checks = evaluate_deterministic(case, response)
    empty_check = next(c for c in checks if c.check_name == "empty_output_detection")
    assert not empty_check.passed

def test_deterministic_evaluator_json_schema_validation():
    case = EvalCase(
        id="TC-JSON",
        dataset_version="v1.0",
        difficulty="medium",
        tags=["json"],
        input="JSON please",
        expected_behavior="Returns JSON",
        evaluation_criteria={"requires_json": True, "required_json_keys": ["date", "activity"]}
    )
    valid_resp = ChatbotResponse(query="JSON please", answer='{"date": "21 Nov", "activity": "Mall"}')
    checks = evaluate_deterministic(case, valid_resp)
    assert all(c.passed for c in checks)

    invalid_resp = ChatbotResponse(query="JSON please", answer='Not a json string at all!')
    bad_checks = evaluate_deterministic(case, invalid_resp)
    json_check = next(c for c in bad_checks if c.check_name == "json_schema_validity")
    assert not json_check.passed

def test_judge_evaluator_returns_structured_score():
    mock_provider = DeterministicMockProvider()
    judge = LLMJudgeEvaluator(provider=mock_provider)
    case = EvalCase(
        id="TC-001",
        dataset_version="v1.0",
        difficulty="easy",
        tags=["flights"],
        input="What is my flight?",
        expected_behavior="Flight EK565",
        evaluation_criteria={}
    )
    response = ChatbotResponse(query="What is my flight?", answer="Flight EK565 at 15:30")
    score = judge.evaluate(case, response)
    assert score.overall_score >= 4.0
    assert score.relevance >= 4
    assert score.groundedness >= 4
    assert score.rubric_version == "v1.2"
