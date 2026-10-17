"""
Schemas for AI Evaluation Cases, Results, and Run Reports.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class EvalCase:
    id: str
    dataset_version: str
    difficulty: str
    tags: List[str]
    input: str
    expected_behavior: str
    evaluation_criteria: Dict[str, Any]

@dataclass
class DeterministicCheckResult:
    check_name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class JudgeScore:
    relevance: int = 0
    groundedness: int = 0
    completeness: int = 0
    instruction_following: int = 0
    overall_score: float = 0.0
    reasoning: str = ""
    evidence: str = ""
    rubric_version: str = "v1.0"
    judge_model: str = ""

@dataclass
class CaseResult:
    case_id: str
    input: str
    output: str
    latency_ms: float
    passed: bool
    failure_reasons: List[str] = field(default_factory=list)
    deterministic_checks: List[DeterministicCheckResult] = field(default_factory=list)
    judge_score: Optional[JudgeScore] = None
    trace_id: Optional[str] = None
    status: str = "SUCCESS"

@dataclass
class EvalRunReport:
    run_id: str
    timestamp: str
    dataset_path: str
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    pass_rate_pct: float = 0.0
    avg_latency_ms: float = 0.0
    results: List[CaseResult] = field(default_factory=list)
    judge_enabled: bool = False
    judge_summary: Dict[str, Any] = field(default_factory=dict)
    comparison: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
