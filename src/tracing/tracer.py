"""
Execution tracer and telemetry recorder.
"""
import os
import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.tracing.models import Span, TraceRecord

logger = logging.getLogger("TripChatbotTracer")

class Tracer:
    """Manages spans, records latencies, and writes structured traces to disk."""

    def __init__(self, trace_dir: str = "traces", enabled: bool = True):
        self.trace_dir = Path(trace_dir)
        self.enabled = enabled
        self._current_trace: Optional[TraceRecord] = None
        self._trace_history: List[TraceRecord] = []
        
        if self.enabled:
            self.trace_dir.mkdir(parents=True, exist_ok=True)

    def start_trace(self, query: str = "", pipeline_version: str = "1.0.0") -> TraceRecord:
        record = TraceRecord(query=query, pipeline_version=pipeline_version)
        self._current_trace = record
        return record

    @contextmanager
    def span(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager to measure and trace an execution span."""
        if not self.enabled or not self._current_trace:
            yield None
            return

        span_obj = Span(name=name, metadata=metadata or {})
        self._current_trace.spans.append(span_obj)
        try:
            yield span_obj
            span_obj.finish(status="SUCCESS")
        except Exception as e:
            span_obj.finish(status="ERROR", error=str(e))
            raise

    def end_trace(self, status: str = "SUCCESS", error: Optional[str] = None, save: bool = True) -> TraceRecord:
        if not self._current_trace:
            return TraceRecord()
        
        record = self._current_trace
        record.finish(status=status, error=error)
        self._trace_history.append(record)
        
        if self.enabled and save:
            self._save_trace_to_disk(record)
            
        self._current_trace = None
        return record

    def _save_trace_to_disk(self, record: TraceRecord):
        try:
            trace_file = self.trace_dir / f"{record.trace_id}.json"
            with open(trace_file, "w", encoding="utf-8") as f:
                json.dump(record.to_dict(), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist trace {record.trace_id}: {e}")

    @property
    def current_trace(self) -> Optional[TraceRecord]:
        return self._current_trace

    @property
    def history(self) -> List[TraceRecord]:
        return self._trace_history

# Global default tracer instance
default_tracer = Tracer()
