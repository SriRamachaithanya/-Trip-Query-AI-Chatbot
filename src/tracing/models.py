"""
Data models for structured tracing and observability.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import time
import uuid

@dataclass
class Span:
    name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "IN_PROGRESS"  # IN_PROGRESS, SUCCESS, ERROR
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    def finish(self, status: str = "SUCCESS", error: Optional[str] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status
        if error:
            self.error_message = str(error)

@dataclass
class TraceRecord:
    trace_id: str = field(default_factory=lambda: f"tr_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)
    query: str = ""
    pipeline_version: str = "1.0.0"
    spans: List[Span] = field(default_factory=list)
    total_latency_ms: float = 0.0
    status: str = "SUCCESS"  # SUCCESS, ERROR
    error: Optional[str] = None
    token_usage: Dict[str, int] = field(default_factory=dict)
    estimated_cost_usd: float = 0.0

    def finish(self, status: str = "SUCCESS", error: Optional[str] = None):
        if self.spans:
            self.total_latency_ms = round(sum(s.duration_ms for s in self.spans), 2)
        self.status = status
        if error:
            self.error = str(error)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data
