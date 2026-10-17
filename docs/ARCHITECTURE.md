# Architecture Design: Trip Query AI Chatbot

**Project:** Trip Query AI Chatbot (FOXO AI Engineering Standard)  
**Document Status:** Target Architecture Specification  
**Last Updated:** October 17, 2026  

---

## 1. Overview & Architectural Goals

The goal of this architectural upgrade is to elevate the **Trip Query AI Chatbot** from a basic two-script RAG prototype into a production-grade, observable, and systematically evaluated AI engineering system.

### Key Architectural Principles
1. **Modularity & Decoupling:** Business logic, vector retrieval, LLM interaction, evaluation, and tracing must operate through clean, well-defined interfaces.
2. **Deterministic Testability:** The entire application and evaluation harness must be capable of running offline in continuous integration (CI) without requiring access to a live GPU/Ollama instance.
3. **Deep Observability:** Every execution step (query parsing, vector retrieval, prompt generation, model invocation) must yield structured telemetry traces.
4. **Rigorous Quality Gateways:** Model outputs are evaluated through a two-tier evaluation framework:
   - **Tier 1 (Deterministic):** Fast, non-negotiable assertions (JSON schema, day counts, price calculations, hallucination red flags).
   - **Tier 2 (Judge-based):** Calibrated LLM-as-judge scoring for relevance, completeness, groundedness, and instruction adherence.

---

## 2. Current Architecture vs. Proposed Target Architecture

### 2.1 Current Architecture (As Audited)

```mermaid
graph TD
    User([Terminal User]) -->|Raw Query| MainScript[main.py: While Loop]
    MainScript -->|Query| VectorScript[vector.py: retriever k=1]
    VectorScript -->|Embed Query| OllamaEmbed[OllamaEmbeddings mxbai-embed-large]
    OllamaEmbed -->|Query Vector| ChromaDB[(Chroma DB: ./chrome_lamgchain_db)]
    ChromaDB -->|Single Document| VectorScript
    VectorScript -->|Document 'reviews'| MainScript
    MainScript -->|Format Prompt| OllamaLLM[OllamaLLM llama3.2]
    OllamaLLM -->|Unchecked Text| MainScript
    MainScript -->|print()| Output([Terminal Output])
```

#### Limitations of Current Architecture:
- Single execution mode (interactive REPL only).
- Hardcoded dependency on local Ollama server.
- Single retrieval document (`k=1`) discarding rich itinerary metadata.
- Zero telemetry, logging, or error isolation.
- No schema enforcement on outputs.
- Ingestion (`vector.py`) tightly coupled to specific hardcoded paths and buggy CSV schemas.

---

### 2.2 Proposed Target Architecture

```mermaid
graph TB
    subgraph Interfaces ["User & Evaluation Interfaces"]
        CLI["CLI Query Interface\n(src/cli.py)"]
        EvalRunner["Evaluation Runner\n(src/evals/runner.py)"]
        APIServer["REST / Python API\n(src/api.py)"]
    end

    subgraph Observability ["Observability & Tracing Layer (src/tracing/)"]
        Tracer["Trace Context & Span Collector"]
        TraceExporter["JSON & Console Trace Exporter"]
        Tracer --> TraceExporter
    end

    subgraph CoreEngine ["RAG & AI Core Engine (src/core/)"]
        Config["Config & Environment\n(src/core/config.py)"]
        Pipeline["RAG Pipeline Orchestrator\n(src/core/pipeline.py)"]
        PromptMgr["Prompt Management\n(src/core/prompts.py)"]
        ResponseParser["Structured Response Parser\n(src/core/schemas.py)"]
    end

    subgraph Retrieval ["Vector & Knowledge Store (src/retrieval/)"]
        DataIngest["CSV Ingestion & Normalizer\n(src/retrieval/ingest.py)"]
        KnowledgeBase[("Dubai_trip.csv")]
        VectorStore["Vector Store Wrapper\n(Chroma / In-Memory Mock)"]
    end

    subgraph Providers ["Model Provider Layer (src/providers/)"]
        ProviderInterface["Base LLM / Embed Provider"]
        OllamaProvider["Ollama Provider\n(Local llama3.2)"]
        OpenAIProvider["OpenAI / Cloud Provider\n(API Compatible)"]
        MockProvider["Deterministic Mock Provider\n(For Offline CI & Tests)"]
    end

    subgraph EvaluationHarness ["Evaluation Harness (src/evals/)"]
        Dataset["Versioned Dataset\n(evals/datasets/v1.jsonl)"]
        DeterministicEval["Deterministic Evaluators\n(Schema, Days, Math, Out-of-Scope)"]
        JudgeEval["LLM-as-Judge Evaluator\n(Relevance, Groundedness)"]
        EvalReports["Evaluation Reports & Metrics\n(evals/reports/*.json)"]
    end

    CLI --> Pipeline
    EvalRunner --> Pipeline
    APIServer --> Pipeline

    Pipeline --> Tracer
    Pipeline --> Retrieval
    Pipeline --> Providers
    Pipeline --> PromptMgr
    Pipeline --> ResponseParser

    DataIngest --> KnowledgeBase
    DataIngest --> VectorStore
    Retrieval --> VectorStore

    Providers --> ProviderInterface
    ProviderInterface <|-- OllamaProvider
    ProviderInterface <|-- OpenAIProvider
    ProviderInterface <|-- MockProvider

    EvalRunner --> Dataset
    EvalRunner --> DeterministicEval
    EvalRunner --> JudgeEval
    EvalRunner --> EvalReports
```

---

## 3. Component Breakdown: Existing vs. Planned

| Component | Current State | Planned Target State |
|---|---|---|
| **Entry Point** | `main.py` (infinite REPL loop) | Modular `src/cli.py` + backwards-compatible `main.py` wrapper |
| **Ingestion** | `vector.py` (breaks on CSV schema error) | `src/retrieval/ingest.py` (schema validation, metadata enrichment, whitespace trimming, CLI rebuild command) |
| **Knowledge Base** | Corrupted CSV + stale committed DB | Cleaned `Dubai_trip.csv` with standardized columns + deterministic indexing |
| **Retrieval Strategy** | `k=1` (text only) | Configurable `k=4` with metadata fusion (Date, Activity, Timing, Location, Meals, Hotel) |
| **LLM Provider** | Hardcoded `langchain_ollama.OllamaLLM` | Pluggable Provider Interface (`Ollama`, `OpenAICompatible`, `DeterministicMock`) |
| **Prompt Management** | Hardcoded string with typo in `main.py` | Versioned templates with few-shot guidance & strict output structuring |
| **Output Schema** | Raw string | Typed output models (Pydantic / Dataclasses) with answer, sources, confidence, and metadata |
| **Tracing** | None | End-to-end tracing capturing: Trace ID, spans, latencies, tokens, prompt snapshots, errors |
| **Evaluation Dataset** | None | Versioned JSONL (`evals/datasets/v1.jsonl`) with 30+ edge cases and ground truth constraints |
| **Deterministic Evals** | None | Suite of rule-based checkers: schema validity, day counts, budget arithmetic, negative rejection |
| **LLM Judge** | None | Multi-metric judge (relevance, groundedness, completeness) with structured reasoning and confidence |
| **Test Suite** | None | Unit tests, integration tests, and regression tests runnable via `pytest` |
| **Configuration** | Hardcoded in Python | Environment variables managed via `.env` and `pydantic-settings` or clean config loader |

---

## 4. Tracing & Telemetry Architecture

Every query entering the pipeline creates a unique `TraceContext`:
```json
{
  "trace_id": "tr_68f7b3a19e2",
  "timestamp": "2026-10-17T13:30:00Z",
  "query": "What are my flights to Dubai and back?",
  "pipeline_version": "v1.2.0",
  "spans": [
    {
      "name": "retrieval",
      "duration_ms": 14.2,
      "metadata": {
        "k": 4,
        "hits_count": 2,
        "document_ids": ["0", "8"]
      }
    },
    {
      "name": "prompt_construction",
      "duration_ms": 0.8,
      "metadata": {
        "template_id": "trip_qa_v1",
        "context_token_estimate": 145
      }
    },
    {
      "name": "llm_generation",
      "duration_ms": 412.5,
      "metadata": {
        "provider": "ollama",
        "model": "llama3.2",
        "temperature": 0.0,
        "prompt_tokens": 180,
        "completion_tokens": 75,
        "estimated_cost_usd": 0.0
      }
    }
  ],
  "total_latency_ms": 427.5,
  "status": "SUCCESS",
  "error": null
}
```

---

## 5. Evaluation Harness Architecture

The evaluation harness operates independently of live external infrastructure when running deterministic evaluations.

### Evaluation Workflow
1. **Dataset Loading:** Validates JSONL schema for test case definitions (input, expected behavior, criteria, tags).
2. **Pipeline Execution:** Passes case inputs through the RAG pipeline.
3. **Tier 1 (Deterministic Checkers):**
   - **Schema Conformance:** Verifies JSON or formatted output structure.
   - **Grounding & Negation Assertions:** Verifies out-of-scope queries (e.g., "book a flight to Paris") politely refuse or clarify.
   - **Fact Matching:** Checks key facts (e.g., flight numbers EK565, hotel names Address Downtown / Hilton Jumeirah).
   - **Arithmetic Checks:** Validates budget and day counting calculations.
4. **Tier 2 (Judge Scoring):**
   - Evaluates subjective qualities (clarity, completeness, helpfulness) using a defined rubric.
   - Outputs score (1–5) with evidence excerpts.
5. **Report Generation:** Produces machine-readable JSON metrics (`evals/reports/eval_*.json`) and terminal summary tables.
6. **Regression Diffing:** Compares new run pass rates against baseline scores to alert on any degradations.
