"""
Typed schemas for RAG inputs, retrieved documents, and generated responses.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class RetrievedDocument:
    id: str
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None

@dataclass
class ChatbotResponse:
    query: str
    answer: str
    sources: List[RetrievedDocument] = field(default_factory=list)
    trace_id: Optional[str] = None
    status: str = "SUCCESS"  # SUCCESS, ERROR, REFUSAL
    error: Optional[str] = None
    latency_ms: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    is_refusal: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "sources": [{"id": s.id, "content": s.page_content, "metadata": s.metadata} for s in self.sources],
            "trace_id": self.trace_id,
            "status": self.status,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "token_usage": self.token_usage,
            "is_refusal": self.is_refusal
        }
