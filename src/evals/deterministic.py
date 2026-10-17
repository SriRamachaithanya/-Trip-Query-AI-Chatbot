"""
Deterministic Rule-Based Evaluators for AI Chatbot Outputs.
"""
import re
import json
from typing import List, Dict, Any
from src.core.schemas import ChatbotResponse
from src.evals.schemas import EvalCase, DeterministicCheckResult

def evaluate_deterministic(case: EvalCase, response: ChatbotResponse) -> List[DeterministicCheckResult]:
    """Runs all applicable rule-based deterministic checks against a response."""
    checks: List[DeterministicCheckResult] = []
    output = response.answer
    criteria = case.evaluation_criteria

    # 1. Empty Output Detection
    is_empty = not output or not output.strip()
    checks.append(DeterministicCheckResult(
        check_name="empty_output_detection",
        passed=not is_empty,
        message="Output is non-empty" if not is_empty else "Response output was empty"
    ))

    # 2. Minimum Length Check
    min_length = criteria.get("min_length", 10)
    passed_min_len = len(output.strip()) >= min_length
    checks.append(DeterministicCheckResult(
        check_name="min_length_check",
        passed=passed_min_len,
        message=f"Length {len(output.strip())} >= {min_length}" if passed_min_len else f"Length {len(output.strip())} < {min_length}"
    ))

    # 3. Required Keywords Check
    required_keywords = criteria.get("required_keywords", [])
    if required_keywords:
        missing_kw = [kw for kw in required_keywords if kw.lower() not in output.lower()]
        passed_kw = len(missing_kw) == 0
        checks.append(DeterministicCheckResult(
            check_name="required_keywords",
            passed=passed_kw,
            message="All required keywords present" if passed_kw else f"Missing required keywords: {missing_kw}"
        ))

    # 4. Prohibited Keywords Check
    prohibited_keywords = criteria.get("prohibited_keywords", [])
    if prohibited_keywords:
        found_prohibited = [kw for kw in prohibited_keywords if kw.lower() in output.lower()]
        passed_prohibited = len(found_prohibited) == 0
        checks.append(DeterministicCheckResult(
            check_name="prohibited_keywords",
            passed=passed_prohibited,
            message="No prohibited keywords detected" if passed_prohibited else f"Found prohibited keywords: {found_prohibited}"
        ))

    # 5. Out-of-Scope Refusal Detection
    if criteria.get("out_of_scope_detected", False) or criteria.get("expected_status") == "REFUSAL":
        refusal_phrases = ["cannot", "apologize", "out of scope", "only assist", "specialized exclusively", "unable to assist", "not part of"]
        passed_refusal = any(phrase in output.lower() for phrase in refusal_phrases) or response.is_refusal or response.status == "REFUSAL"
        checks.append(DeterministicCheckResult(
            check_name="out_of_scope_refusal",
            passed=passed_refusal,
            message="Out-of-scope query was politely refused" if passed_refusal else "Failed to refuse out-of-scope query"
        ))

    # 6. JSON Schema Validity Check
    if criteria.get("requires_json", False):
        try:
            # Extract JSON block if wrapped in markdown
            json_text = output
            if "```json" in output:
                json_text = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                json_text = output.split("```")[1].split("```")[0].strip()
            
            parsed_json = json.loads(json_text)
            passed_json = True
            msg = "Valid JSON syntax parsed"
            
            # Check required keys if dict
            required_json_keys = criteria.get("required_json_keys", [])
            if required_json_keys and isinstance(parsed_json, dict):
                missing_keys = [k for k in required_json_keys if k not in parsed_json]
                if missing_keys:
                    passed_json = False
                    msg = f"JSON missing required keys: {missing_keys}"

        except Exception as e:
            passed_json = False
            msg = f"Failed to parse JSON: {e}"

        checks.append(DeterministicCheckResult(
            check_name="json_schema_validity",
            passed=passed_json,
            message=msg
        ))

    # 7. Day Count Validation
    required_day_count = criteria.get("required_day_count")
    if required_day_count:
        # Match dates in November: 20 Nov, 21 Nov, etc.
        days_found = set(re.findall(r"(?:2[0-5]\s*Nov|Nov\s*2[0-5])", output, re.IGNORECASE))
        passed_days = len(days_found) >= required_day_count
        checks.append(DeterministicCheckResult(
            check_name="day_count_validation",
            passed=passed_days,
            message=f"Found {len(days_found)} days (required {required_day_count}): {list(days_found)}"
        ))

    # 8. Budget Arithmetic Check
    if criteria.get("arithmetic_verified", False):
        passed_arithmetic = "150" in output
        checks.append(DeterministicCheckResult(
            check_name="budget_arithmetic",
            passed=passed_arithmetic,
            message="Arithmetic sum $150 verified" if passed_arithmetic else "Expected sum 150 not found in output"
        ))

    # 9. Budget Groundedness / Unrecorded Price Honesty
    if criteria.get("numerical_budget_claimed") is False:
        # Should not falsely assert exact numerical budget without noting missing info
        unrecorded_markers = ["not recorded", "cannot confirm", "pricing not available", "does not contain", "not specified", "not provided", "price not listed"]
        passed_honesty = any(marker in output.lower() for marker in unrecorded_markers)
        checks.append(DeterministicCheckResult(
            check_name="budget_unsupported_claim_honesty",
            passed=passed_honesty,
            message="Explicitly stated that pricing is unrecorded or unavailable" if passed_honesty else "Falsely affirmed ungrounded budget or omitted unrecorded status"
        ))

    return checks
