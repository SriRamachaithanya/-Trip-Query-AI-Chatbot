"""
Unit tests for structured execution tracing.
"""
import pytest
from src.tracing.tracer import Tracer
from src.tracing.models import TraceRecord, Span

def test_tracer_lifecycle(tmp_path):
    tracer = Tracer(trace_dir=str(tmp_path), enabled=True)
    trace = tracer.start_trace(query="Where is Burj Khalifa?")
    assert trace.trace_id.startswith("tr_")
    assert trace.query == "Where is Burj Khalifa?"

    with tracer.span("retrieval", {"k": 4}) as span:
        assert span.name == "retrieval"
        assert span.status == "IN_PROGRESS"

    assert len(trace.spans) == 1
    assert trace.spans[0].status == "SUCCESS"
    assert trace.spans[0].duration_ms >= 0.0

    completed_trace = tracer.end_trace(status="SUCCESS")
    assert completed_trace.status == "SUCCESS"
    assert len(tracer.history) == 1

    # Verify persisted JSON file
    trace_file = tmp_path / f"{completed_trace.trace_id}.json"
    assert trace_file.exists()

def test_tracer_captures_span_errors(tmp_path):
    tracer = Tracer(trace_dir=str(tmp_path), enabled=True)
    tracer.start_trace(query="Test Error")

    with pytest.raises(ValueError):
        with tracer.span("faulty_operation"):
            raise ValueError("Simulated retrieval failure")

    record = tracer.end_trace(status="ERROR", error="Simulated retrieval failure")
    assert record.status == "ERROR"
    assert record.spans[0].status == "ERROR"
    assert "Simulated retrieval failure" in record.spans[0].error_message
