# Trip Query AI Chatbot (Production AI Engineering Edition)

[![CI & AI Evaluation Pipeline](https://github.com/SriRamachaithanya/-Trip-Query-AI-Chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/SriRamachaithanya/-Trip-Query-AI-Chatbot/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Evaluation Pass Rate](https://img.shields.io/badge/eval%20pass%20rate-100%25-brightgreen.svg)](evals/reports/)
[![Tests](https://img.shields.io/badge/tests-20%20passed-success.svg)](tests/)
[![Architecture](https://img.shields.io/badge/architecture-modular%20RAG-orange.svg)](docs/ARCHITECTURE.md)

An enterprise-ready Retrieval-Augmented Generation (RAG) system engineered for the **FOXO AI Engineering** evaluation. Features deep execution tracing, multi-document context fusion, a two-tiered evaluation harness (deterministic + LLM-as-a-judge), regression tests derived from real failure modes, and pluggable provider abstractions (Ollama, OpenAI, and deterministic offline mock).

---

## 📑 Table of Contents
- [FOXO AI Engineering Competency Matrix](#-foxo-ai-engineering-competency-matrix)
- [System Architecture](#-system-architecture)
- [Documentation Index](#-documentation-index)
- [Core Capabilities](#-core-capabilities)
- [Evaluation Harness & Dataset Taxonomy](#-evaluation-harness--dataset-taxonomy)
- [End-to-End Tracing & Observability](#-end-to-end-tracing--observability)
- [Quick Start & Installation](#-quick-start--installation)
- [Running the Interactive Chatbot](#-running-the-interactive-chatbot)
- [Running the Evaluation Benchmark](#-running-the-evaluation-benchmark)
- [Automated Testing Suite](#-automated-testing-suite)
- [Repository Structure](#-repository-structure)

---

## 🎯 FOXO AI Engineering Competency Matrix

This upgrade directly demonstrates the core capabilities expected of production AI Engineers at FOXO:

| FOXO Expectation | System Implementation | Verification / Evidence |
|---|---|---|
| **Build & Maintain Reliable LLM Apps** | Modular RAG pipeline with provider auto-detection, fallback resilience, and graceful degradation when daemons are offline. | [`src/core/pipeline.py`](src/core/pipeline.py), [`src/providers/`](src/providers/) |
| **Evaluate Model Outputs** | Dual-tier evaluation framework: 9 deterministic rule-based checkers + structured qualitative LLM judge. | [`src/evals/deterministic.py`](src/evals/deterministic.py), [`src/evals/judge.py`](src/evals/judge.py) |
| **Trace Failures & Latency** | Span-based distributed tracing capturing stage durations, token usage, prompt snapshots, and sanitized errors. | [`src/tracing/tracer.py`](src/tracing/tracer.py), [`traces/`](traces/) |
| **Create Regression Tests from Real Failures** | Test suite guarding against historical bugs: inverted hotel check-in order, ungrounded budget assertions, flight code collisions. | [`tests/test_regression.py`](tests/test_regression.py) |
| **Manage Versioned Datasets** | Formal JSONL dataset covering 32 travel queries across 12 challenging edge-case categories. | [`evals/datasets/v1.jsonl`](evals/datasets/v1.jsonl) |
| **Ship CI/CD-Ready Code** | Fully automated GitHub Actions workflow verifying test suites and running evaluation benchmarks on push. | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph Interfaces ["User & Benchmark Interfaces"]
        CLI["CLI Interactive App\n(main.py)"]
        Runner["Evaluation Runner\n(src/evals/runner.py)"]
    end

    subgraph CoreEngine ["RAG Core Orchestration (src/core/)"]
        Config["Config & Environment\n(src/core/config.py)"]
        Pipeline["RAG Pipeline Orchestrator\n(src/core/pipeline.py)"]
        Prompts["Context Fusion & Prompts\n(src/core/prompts.py)"]
    end

    subgraph Observability ["Observability Layer (src/tracing/)"]
        Tracer["Trace Context & Span Manager\n(src/tracing/tracer.py)"]
        TraceDisk[("Trace JSON Dumps\ntraces/*.json")]
        Tracer --> TraceDisk
    end

    subgraph KnowledgeStore ["Knowledge & Ingestion (src/retrieval/)"]
        CSV[("Dubai_trip.csv")]
        Ingest["CSV Sanitizer & Normalizer\n(src/retrieval/ingest.py)"]
        Store["Scoring & Hybrid Retriever\n(src/retrieval/store.py)"]
        CSV --> Ingest --> Store
    end

    subgraph Providers ["Model Provider Layer (src/providers/)"]
        ProviderInterface["BaseLLMProvider"]
        OllamaP["OllamaProvider\n(llama3.2)"]
        OpenAIP["OpenAICompatibleProvider\n(gpt-4o-mini)"]
        MockP["DeterministicMockProvider\n(Offline CI/CD)"]
        ProviderInterface <|-- OllamaP
        ProviderInterface <|-- OpenAIP
        ProviderInterface <|-- MockP
    end

    subgraph EvaluationHarness ["Evaluation Harness (src/evals/)"]
        Dataset[("evals/datasets/v1.jsonl\n(32 Versioned Scenarios)")]
        Deterministic["Deterministic Evaluators\n(Schema, Math, Day Count, Refusal)"]
        Judge["LLM-as-a-Judge\n(Relevance, Groundedness)"]
        Reports[("evals/reports/*.json")]
    end

    CLI --> Pipeline
    Runner --> Pipeline
    Pipeline --> Tracer
    Pipeline --> Store
    Pipeline --> Prompts
    Pipeline --> Providers
    Runner --> Dataset
    Runner --> Deterministic
    Runner --> Judge
    Runner --> Reports
```

---

## 📑 Documentation Index
- **[Codebase Audit](docs/CODEBASE_AUDIT.md):** Pre-upgrade findings, data ingestion bugs, security/reliability risks, and technical debt analysis.
- **[System Architecture](docs/ARCHITECTURE.md):** Target vs. legacy architecture, pipeline data flow, and telemetry designs.
- **[Implementation Plan](docs/IMPLEMENTATION_PLAN.md):** Phased rollout milestones, acceptance criteria, and verification commands.
- **[Baseline Report](docs/BASELINE.md):** Initial setup blockers, dependency audits, and baseline test results.

---

## 🛠️ Core Capabilities

| Capability | Legacy Prototype | FOXO Production Standard |
|---|---|---|
| **Retrieval Depth** | $k=1$ (single row) | $k=4$ with metadata fusion (Dates, Flights, Hotels, Timings) |
| **Provider Support** | Hardcoded Ollama only | Pluggable: Ollama (`llama3.2`), OpenAI (`gpt-4o-mini`), and Offline Mock |
| **Evaluation Suite** | None | 32-case versioned JSONL dataset with deterministic and judge grading |
| **Observability** | None | End-to-end tracing with stage latency profiling and JSON persistence |
| **Testing** | 0 tests | 20 unit, integration, and regression tests runnable via `pytest` |
| **CI/CD Automation** | None | GitHub Actions running automated tests and evaluation benchmarks |
| **CSV Ingestion** | Crashed on column mismatch | Robust whitespace trimming, alias matching, and clean delimiter parsing |

---

## 🧪 Evaluation Harness & Dataset Taxonomy

The evaluation harness evaluates 32 real-world travel queries across 12 distinct behavioral categories:

| Category | Cases | Primary Checks & Assertions |
|---|---|---|
| **Normal Queries** | TC-001 – TC-004 | Verifies outbound/return flight codes, first-night hotel check-in, visit timings. |
| **Multi-Day Itineraries** | TC-005, TC-006 | Asserts full 6-day coverage (Nov 20–25) and marine activity aggregation. |
| **Budget Constraints** | TC-007 – TC-009, TC-031 | Verifies arithmetic ($80 + $70 = $150) and rejects ungrounded price claims. |
| **Missing Information** | TC-010, TC-011 | Tests flight ambiguity handling and multi-date meal breakdowns. |
| **Contradictory Queries** | TC-012, TC-013 | Detects schedule conflicts (Safari vs Abu Dhabi) and inverted hotel orders. |
| **Out-of-Scope Requests** | TC-014 – TC-016 | Asserts polite refusals for Tokyo, Paris car rentals, and physics questions. |
| **Empty Retrieval / Hallucination** | TC-017, TC-018 | Checks negation assertions for non-existent events (Miracle Garden, museum dates). |
| **Unsupported Claims** | TC-019, TC-028 | Flags unsupported schedule additions (Ski Dubai) and Burj ticket warnings. |
| **Structured Output (JSON)** | TC-021, TC-022 | Validates strict JSON syntax and required schema keys. |
| **Robustness & Edge Cases** | TC-023, TC-024 | Checks empty strings, whitespaces, and gibberish handling without crashing. |
| **Logistics & Details** | TC-020, TC-025 – TC-027, TC-029, TC-030 | Validates private transfers, cruise timings, and checkout schedules. |
| **Negative Testing** | TC-032 | Deliberate failure trigger verification to ensure assertions fire reliably. |

---

## 🔍 End-to-End Tracing & Observability

Every query creates a structured `TraceRecord` with span-level timing and metadata persisted to disk:

```json
{
  "trace_id": "tr_016d83f21fb0",
  "timestamp": 1792244528.66,
  "query": "What is my flight from Bangalore to Dubai?",
  "pipeline_version": "2.0.0",
  "spans": [
    {
      "name": "retrieval",
      "duration_ms": 0.42,
      "status": "SUCCESS",
      "metadata": { "k": 4 }
    },
    {
      "name": "prompt_construction",
      "duration_ms": 0.11,
      "status": "SUCCESS"
    },
    {
      "name": "llm_generation",
      "duration_ms": 0.28,
      "status": "SUCCESS",
      "metadata": { "provider": "DeterministicMockProvider" }
    }
  ],
  "total_latency_ms": 0.81,
  "status": "SUCCESS",
  "token_usage": {
    "prompt_tokens": 80,
    "completion_tokens": 28,
    "total_tokens": 108
  }
}
```

---

## 🚀 Quick Start & Installation

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/SriRamachaithanya/-Trip-Query-AI-Chatbot.git
cd -Trip-Query-AI-Chatbot

# Create and activate virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Set LLM_PROVIDER to 'mock', 'ollama', or 'openai'
```

---

## ▶️ Running the Interactive Chatbot

Start the interactive command-line interface:
```bash
python main.py
```
*Note: If Ollama is not running locally, the chatbot automatically and gracefully falls back to the deterministic offline provider, allowing immediate exploration without external daemons.*

Sample interaction:
```
============================================================
🌴 Welcome to the Dubai Trip Query AI Chatbot 🌴
============================================================
Active Provider: DeterministicMockProvider
Type your questions about flights, hotels, activities, and timings.
Type 'q' or 'exit' to quit.

--------------------------------------------------
Ask a query about the Dubai Trip: What is my flight from Bangalore to Dubai?

Response:
Your outbound flight is Emirates EK565 on 20 Nov, departing Bangalore at 15:30 and arriving at DXB Airport at 18:40.

[Trace ID: tr_6ddec6892516 | Latency: 0.62ms | Sources: 4]
```

---

## 🧪 Running the AI Evaluation Harness

The evaluation harness validates response accuracy, schema conformity, budget arithmetic, and hallucination resistance across 32 real-world travel queries.

### Run Deterministic Benchmark (Offline / CI Mode)
```bash
python -m src.evals.runner --provider mock
```

### Run Benchmark with LLM-as-a-Judge Enabled
```bash
python -m src.evals.runner --provider mock --enable-judge
```

### Run Benchmark against Local Ollama (`llama3.2`)
```bash
python -m src.evals.runner --provider ollama --enable-judge
```

### Compare Results with Previous Evaluation Run
```bash
python -m src.evals.runner --provider mock --compare-baseline latest
```

Sample benchmark output:
```
============================================================
EVALUATION RUN SUMMARY
============================================================
+---------------------+----------------------------+
| Metric              | Value                      |
+=====================+============================+
| Total Test Cases    | 32                         |
+---------------------+----------------------------+
| Passed Cases        | [PASS] 32                  |
+---------------------+----------------------------+
| Failed Cases        | [FAIL] 0                   |
+---------------------+----------------------------+
| Pass Rate           | 100.0%                     |
+---------------------+----------------------------+
| Average Latency     | 0.2 ms                     |
+---------------------+----------------------------+
| Judge Evaluator     | Enabled (5.0/5.0)          |
+---------------------+----------------------------+
| Baseline Comparison | Diff: +0.0% (prev: 100.0%) |
+---------------------+----------------------------+
============================================================
```

---

## 🔬 Automated Testing Suite

Run all 20 automated unit, integration, baseline, and regression tests:
```bash
pytest tests/ -v
```

Tests include:
- `test_baseline.py`: Verifies CSV schema, header parsing, `.gitignore` protections, and `.env.example` placeholders.
- `test_eval_harness.py`: Validates dataset loading, deterministic checks, JSON schema parser, and deliberate failure detection.
- `test_tracing.py`: Validates span lifecycles, nested timing, trace ID propagation, and error containment.
- `test_pipeline.py`: Tests full RAG orchestration with multi-document retrieval and out-of-scope refusal.
- `test_regression.py`: Guards against real failure modes (flight code mixing, unrecorded pricing claims, hotel sequence).

---

## 📁 Repository Structure

```
-Trip-Query-AI-Chatbot/
├── .github/workflows/ci.yml       # GitHub Actions CI automated pipeline
├── docs/                          # Engineering & architecture specifications
│   ├── CODEBASE_AUDIT.md          # Comprehensive audit of original prototype
│   ├── ARCHITECTURE.md            # System architecture and telemetry design
│   ├── IMPLEMENTATION_PLAN.md     # Engineering phases and verification gates
│   └── BASELINE.md                # Initial blockers and baseline verification
├── evals/                         # AI Evaluation Harness
│   ├── datasets/v1.jsonl          # 32 versioned benchmark scenarios
│   └── reports/                   # Timestamped JSON evaluation reports
├── src/                           # Production source code
│   ├── core/                      # RAG pipeline, schemas, prompts, config
│   ├── evals/                     # Evaluator runner, deterministic checks, judge
│   ├── providers/                 # Base, Ollama, OpenAI, and Mock providers
│   ├── retrieval/                 # CSV ingestion and scoring store
│   └── tracing/                   # Structured telemetry and span recorder
├── tests/                         # Pytest test suite (20 automated tests)
├── traces/                        # Execution trace JSON dumps
├── Dubai_trip.csv                 # Cleaned and validated itinerary dataset
├── main.py                        # Interactive console CLI
├── vector.py                      # Backwards-compatible retriever export
├── requirements.txt               # Pinned project dependencies
└── pyproject.toml                 # Package definition and pytest configuration
```