# Implementation Plan: Trip Query AI Chatbot

**Target Standard:** Production-Grade AI Engineering Project for FOXO AI Internship  
**Status:** Approved for Implementation Execution  
**Current Date:** October 17, 2026  

---

## 1. Overview & Strategy

This implementation plan details the step-by-step path to transition the repository from its current proof-of-concept state to a robust, production-style AI engineering project.

The plan strictly preserves all existing user code and functionality while introducing:
1. Environment isolation & dependency standardization.
2. Ingestion fixes and vector store hygiene.
3. Provider abstraction for deterministic offline CI and live LLM operation.
4. Comprehensive 30+ scenario AI evaluation harness (deterministic + LLM judge).
5. OpenTelemetry-compatible execution tracing and latency profiling.
6. Regression test suite and continuous integration verification.

---

## 2. Implementation Phases

### Phase 2: Establish a Stable Baseline & Project Hygiene
**Goal:** Clean up the repository, un-track binary artifacts, fix the corrupted CSV data, establish dependency manifests, and create reproducible baseline smoke tests.

- **Tasks:**
  1. Create `.gitignore` to prevent committing `.pyc`, `__pycache__`, local database binaries (`chrome_lamgchain_db`), virtual environments, and `.env` files.
  2. Preserve uncommitted changes in `readme.md`.
  3. Clean up `Dubai_trip.csv`:
     - Remove empty leading line.
     - Fix column header spacing.
     - Fix broken quotation delimiters on rows with commas in text (`"Arrival, private hotel transfer"` and `"Palm Jumeirah, Atlantis"`).
     - Standardize column naming (`Highlights` vs `Attractions / Details`).
  4. Create `requirements.txt` and `pyproject.toml` specifying pinned dependencies (`pandas`, `chromadb`, `langchain-core`, `langchain-chroma`, `langchain-ollama`, `pydantic`, `pytest`, `tabulate`).
  5. Create `.env.example` documenting all configuration keys (`LLM_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `EMBEDDING_MODEL`, `OPENAI_API_KEY`, etc.).
  6. Create `docs/BASELINE.md` documenting current baseline runtime blockers (e.g. missing Ollama instance, missing packages) and setup instructions.
  7. Add a baseline smoke test to verify imports, CSV parsing, and document mapping without requiring external network calls.

- **Files to Create / Modify:**
  - `.gitignore` (New)
  - `requirements.txt` (New)
  - `pyproject.toml` (New)
  - `.env.example` (New)
  - `Dubai_trip.csv` (Fix formatting)
  - `docs/BASELINE.md` (New)
  - `tests/test_baseline.py` (New)

- **Acceptance Criteria:**
  - `.gitignore` ignores `__pycache__`, `.env`, and database stores.
  - CSV parsing works cleanly in `pandas` with 7 standard columns and zero malformed rows.
  - Baseline smoke tests pass.
  - Blockers regarding external services (Ollama) are documented transparently.

---

### Phase 3: Build a Reliable AI Evaluation Harness
**Goal:** Build a benchmark dataset and multi-tiered evaluation framework to validate RAG output quality, schema compliance, and groundedness.

- **Tasks:**
  1. **Dataset Creation (`evals/datasets/v1.jsonl`):**
     - Construct a versioned dataset of at least 30 diverse travel queries.
     - Include normal questions, multi-day itinerary generation, budget queries, missing info, contradictory requests, out-of-scope travel requests, empty retrieval responses, malformed requests, and flight queries.
     - Schema fields: `id`, `input`, `expected_behavior`, `evaluation_criteria`, `tags`, `difficulty`, `dataset_version`.
  2. **Deterministic Evaluator Engine (`src/evals/deterministic.py`):**
     - Schema validation (JSON / structured field existence).
     - Itinerary day counter (validating expected days against returned output).
     - Fact verification (flights EK565/EK566, hotels Address Downtown/Hilton Jumeirah).
     - Out-of-scope refusal check (ensuring model politely declines ungrounded destinations like Tokyo/Paris).
     - Budget / arithmetic checking.
     - Empty response & error format checks.
  3. **LLM-as-Judge Evaluator (`src/evals/judge.py`):**
     - Optional judge scoring model evaluating Relevance, Groundedness, Completeness, and Instruction Following.
     - Returns structured JSON: score (1–5), concise reasoning, and evidence quotation.
     - Fully optional: runs only when judge API key or Ollama model is configured.
  4. **Evaluation Runner CLI (`src/evals/runner.py`):**
     - CLI flags: `--dataset`, `--provider`, `--enable-judge`, `--save-report`, `--compare-baseline`.
     - Output concise terminal summary table and full machine-readable JSON reports in `evals/reports/`.
     - Calculates pass rates, average latency, and score distributions.
     - Supports diffing against previous evaluation run reports to flag regressions.

- **Files to Create / Modify:**
  - `evals/datasets/v1.jsonl` (New)
  - `src/evals/__init__.py` (New)
  - `src/evals/schemas.py` (New)
  - `src/evals/deterministic.py` (New)
  - `src/evals/judge.py` (New)
  - `src/evals/runner.py` (New)
  - `evals/reports/.gitkeep` (New)
  - `tests/test_eval_harness.py` (New)

- **Acceptance Criteria:**
  - Evaluation runner executes cleanly from command line without requiring manual code edits.
  - Deterministic evaluation runs 100% offline without requiring paid API keys or live Ollama servers (using Mock Provider or cached pipeline).
  - Deliberately flawed/failing cases are correctly flagged as failures.
  - JSON reports saved with accurate latency and pass/fail statistics.

---

### Phase 4: Implement End-to-End Tracing & Observability
**Goal:** Introduce deep execution telemetry across every stage of the RAG pipeline.

- **Tasks:**
  1. Build a lightweight `Tracer` and `TraceContext` in `src/tracing/tracer.py`.
  2. Propagate a unique `trace_id` through every pipeline phase:
     - Retrieval span (k, document IDs, retrieval latency).
     - Prompt span (template name, token estimates).
     - LLM generation span (model name, provider, duration, token usage, error status).
  3. Support local JSON file trace logging and console debugging logs.
  4. Ensure all exceptions are captured, sanitized, and attributed to the exact failing span.

- **Files to Create / Modify:**
  - `src/tracing/__init__.py` (New)
  - `src/tracing/tracer.py` (New)
  - `src/tracing/models.py` (New)
  - `tests/test_tracing.py` (New)

- **Acceptance Criteria:**
  - Each request produces a trace with a distinct UUID.
  - Latency is measured per span and summed for the total request.
  - Errors during retrieval or model calls attach cleanly to the failing span without crashing the trace collector.

---

### Phase 5: Modular Core Engine & Provider Abstraction
**Goal:** Refactor the core pipeline to support multiple providers (Ollama, OpenAI-compatible, Deterministic Mock) and improved retrieval (`k=4`, metadata fusion) while maintaining full backwards compatibility for `main.py` and `vector.py`.

- **Tasks:**
  1. Create `src/providers/` with `BaseProvider`, `OllamaProvider`, `OpenAIProvider`, and `MockProvider`.
  2. Fix `vector.py` and create `src/retrieval/` with robust CSV ingestion, metadata serialization, and configurable retriever.
  3. Create `src/core/pipeline.py` orchestrating tracing, retrieval, prompt formatting, and structured response generation.
  4. Update `main.py` to seamlessly wrap the improved pipeline while retaining the familiar interactive command-line interface.

- **Files to Create / Modify:**
  - `src/providers/__init__.py`, `base.py`, `ollama.py`, `mock.py` (New)
  - `src/retrieval/__init__.py`, `ingest.py`, `store.py` (New)
  - `src/core/__init__.py`, `config.py`, `pipeline.py`, `prompts.py` (New)
  - `vector.py` (Updated to use robust ingestion)
  - `main.py` (Updated to leverage modular pipeline with graceful fallback)

- **Acceptance Criteria:**
  - `python main.py` functions as expected.
  - Pipeline can run seamlessly with `--mock` or `LLM_PROVIDER=mock` for testing.
  - Ingestion does not crash on re-indexing.

---

### Phase 6: Regression Testing, CI/CD, and Documentation
**Goal:** Deliver a rock-solid, production-ready GitHub repository with test automation and clear documentation for the FOXO evaluation panel.

- **Tasks:**
  1. Create regression test suite in `tests/test_regression.py` derived from real edge cases (e.g., flight queries, out-of-bounds dates, empty queries).
  2. Configure GitHub Actions workflow in `.github/workflows/ci.yml` running linter, unit tests, and evaluation runner on every push.
  3. Write comprehensive documentation in `docs/` and update `README.md` (while incorporating existing user content).

- **Files to Create / Modify:**
  - `tests/test_regression.py` (New)
  - `.github/workflows/ci.yml` (New)
  - `README.md` (Updated with complete architectural documentation)

---

## 3. Verification & Validation Commands

| Verification Step | Command |
|---|---|
| Run Smoke & Baseline Tests | `python -m pytest tests/test_baseline.py -v` |
| Run Full Unit Test Suite | `python -m pytest tests/ -v` |
| Execute Deterministic Evaluation Run | `python -m src.evals.runner --dataset evals/datasets/v1.jsonl --provider mock` |
| Execute Evaluation with Ollama | `python -m src.evals.runner --dataset evals/datasets/v1.jsonl --provider ollama` |
| Inspect Evaluation Reports | `python -c "import glob, json; print(json.load(open(sorted(glob.glob('evals/reports/*.json'))[-1])))"` |
| Run Interactive Chatbot | `python main.py` |
