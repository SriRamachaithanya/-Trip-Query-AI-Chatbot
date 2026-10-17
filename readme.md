# Trip Query AI Chatbot (Production-Style AI Engineering Edition)

[![CI & AI Evaluation Pipeline](https://github.com/SriRamachaithanya/-Trip-Query-AI-Chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/SriRamachaithanya/-Trip-Query-AI-Chatbot/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Evaluation Pass Rate](https://img.shields.io/badge/eval%20pass%20rate-100%25-brightgreen.svg)](evals/reports/)

An enterprise-ready Retrieval-Augmented Generation (RAG) system upgraded for the **FOXO AI Engineering** standard. Features deep execution tracing, multi-document context fusion, deterministic and LLM-as-a-judge evaluation harnesses, regression testing from real failure modes, and pluggable provider abstractions (Ollama, OpenAI, and deterministic offline mock).

---

## 📑 Documentation Index
- **[Codebase Audit](docs/CODEBASE_AUDIT.md):** Initial findings, data ingestion bugs, security/reliability risks, and technical debt analysis.
- **[System Architecture](docs/ARCHITECTURE.md):** Target vs. legacy architecture, pipeline data flow, and telemetry designs.
- **[Implementation Plan](docs/IMPLEMENTATION_PLAN.md):** Phased rollout milestones, acceptance criteria, and verification commands.
- **[Baseline Report](docs/BASELINE.md):** Initial setup blockers, dependency audits, and baseline test results.

---

## 💡 How It Works

The system operates across four coordinated layers:

1. **Ingestion & Knowledge Store (`src/retrieval/`):** Reads and validates `Dubai_trip.csv`, sanitizes column whitespace, parses quoted text safely, and stores rich metadata (Dates, Timing, Locations, Flights, Meals, Hotels).
2. **Observability & Tracing (`src/tracing/`):** Generates a unique `TraceRecord` with span-level timing for retrieval, prompt formatting, and model completion, recording token counts and errors to disk (`traces/*.json`).
3. **Core Orchestration (`src/core/`):** Performs multi-document retrieval ($k=4$), dynamically builds context, and invokes the configured model provider.
4. **Evaluation Harness (`src/evals/`):** Runs a 32-scenario versioned benchmark dataset (`evals/datasets/v1.jsonl`) against deterministic assertions and an optional qualitative LLM judge, generating machine-readable comparison reports (`evals/reports/`).

---

## 🛠️ Key Capabilities

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

## ▶️ Running the Chatbot

Start the interactive command-line interface:
```bash
python main.py
```
*Note: If Ollama is not running locally, the chatbot automatically and gracefully falls back to the deterministic offline provider, allowing immediate exploration without external daemons.*

Sample interaction:
```
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

Sample output:
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
| Baseline Comparison | Diff: +0.0% (prev: 100.0%) |
+---------------------+----------------------------+
============================================================
```

---

## 🔬 Automated Testing

Run the complete test suite including baseline validation, tracing checks, pipeline integration, and regression suites:
```bash
pytest tests/ -v
```

---

## 📁 Repository Structure

```
-Trip-Query-AI-Chatbot/
├── .github/workflows/ci.yml       # GitHub Actions CI automated pipeline
├── docs/                          # Engineering & architecture specifications
│   ├── CODEBASE_AUDIT.md
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── BASELINE.md
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