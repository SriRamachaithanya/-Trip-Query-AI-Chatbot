# Codebase Audit: Trip Query AI Chatbot

**Audited Repository:** `SriRamachaithanya/-Trip-Query-AI-Chatbot`  
**Date of Audit:** October 17, 2026  
**Auditor Role:** Senior AI Engineer & Evaluator (FOXO AI Engineering Preparation)  
**Verification Status:** Verified against local repository inspection and runtime checks.

---

## 1. Executive Summary

The **Trip Query AI Chatbot** repository is an early-stage proof-of-concept (PoC) Retrieval-Augmented Generation (RAG) system built to answer travel itinerary queries for a trip to Dubai. 

While the concept demonstrates core RAG mechanics (vector embeddings + persistent vector storage + LLM synthesis), the codebase currently lacks production engineering standards required for enterprise AI systems and the FOXO AI Engineering selection criteria:
- **No Evaluation Harness:** No evaluation dataset, deterministic evaluators, or LLM-as-judge scoring.
- **No Observability or Tracing:** No trace IDs, latency metrics, stage timing, prompt logging, or token accounting.
- **Critical Ingestion & Schema Bugs:** Ingestion script `vector.py` crashes on a `KeyError` when attempting to build the database from `Dubai_trip.csv` due to column naming mismatches and malformed CSV rows.
- **Severe Retrieval Bottleneck:** Vector search is hardcoded to `k=1`, rendering multi-day queries, flight lookups, and schedule aggregation impossible.
- **Hardcoupled Provider Dependency:** Hard-coded to local Ollama (`llama3.2` and `mxbai-embed-large`) with no abstraction layer, offline mocks, or fallback support for CI/CD.
- **Git & Dependency Hygiene Deficits:** Committed Python bytecode (`.pyc`), committed local database binaries (`chrome_lamgchain_db`), no `.gitignore`, no `requirements.txt`, no `.env.example`, and zero automated tests.

---

## 2. Repository Layout & File Inventory

```
-Trip-Query-AI-Chatbot/
├── .git/                      # Git repository (Branch: main, 2 commits)
├── __pycache__/               # COMITTED ARTIFACT: vector.cpython-313.pyc (Python 3.13 bytecode)
├── chrome_lamgchain_db/       # COMMITTED ARTIFACT: Local Chroma DB (typographic naming: "chrome_lamgchain_db")
│   ├── 0c0554aa-.../          # HNSW index binary files
│   └── chroma.sqlite3         # SQLite database containing 54 metadata rows, 9 documents
├── Dubai_trip.csv             # Raw travel itinerary CSV data (Contains CSV formatting errors)
├── main.py                    # Interactive console REPL (LangChain ChatPromptTemplate + OllamaLLM)
├── readme.md                  # Project documentation (uncommitted working tree changes present)
└── vector.py                  # Ingestion logic & retriever export (Chroma + OllamaEmbeddings)
```

### Missing Files & Standards
- `requirements.txt` / `pyproject.toml`: Missing; dependencies are unpinned.
- `.gitignore`: Missing; binary cache and database files are currently tracked in Git.
- `.env` / `.env.example`: Missing; configuration is hardcoded in Python code.
- `tests/`: Missing; no unit tests, integration tests, or smoke tests.
- `evals/`: Missing; no versioned benchmark datasets, evaluation runners, or scorecards.
- `tracing/`: Missing; no telemetry, spans, or request tracking.

---

## 3. Architecture & Data Flow Analysis

### Current Ingestion Pipeline (`vector.py`)
```
[Dubai_trip.csv]
       │
       ▼ (pandas.read_csv)
  Parsed DataFrame
       │
       ▼ (Iterates rows; maps Date + Activity to page_content; extracts metadata)
 LangChain Document List
       │
       ▼ (OllamaEmbeddings: mxbai-embed-large)
 [Chroma Vector Store] (./chrome_lamgchain_db)
```
- **Conditional Ingestion Logic:** `add_documents = not os.path.exists(db_location)`. If the directory exists, document ingestion is bypassed entirely.
- **Retriever Export:** Exports `retriever = vector_store.as_retriever(search_kwargs={"k": 1})`.

### Current Runtime Query Pipeline (`main.py`)
```
[User Terminal Input]
       │
       ▼ (input loop in while True)
 Query String
       │
       ▼ (retriever.invoke(question))
 Single Document (k=1)
       │
       ▼ (ChatPromptTemplate formatting)
 Prompt String: "Here are some relevent information:{reviews}\nHere are the questions to answers:{question}"
       │
       ▼ (OllamaLLM: llama3.2)
 Raw Response Text
       │
       ▼ (print to stdout)
 Terminal Output
```

---

## 4. Key Findings, Bugs, and Vulnerabilities

### Finding 1: Fatal Column Mismatch in CSV Ingestion (HIGH SEVERITY)
- **Location:** `vector.py:25`
- **Details:** `vector.py` attempts to read `row["Attractions / Details"]`. However, the header in `Dubai_trip.csv` defines this column as `Highlights`.
- **Impact:** Any attempt to ingest from `Dubai_trip.csv` (e.g., when `chrome_lamgchain_db` is deleted or on a clean environment) raises `KeyError: 'Attractions / Details'`.
- **Verification:** Verified by inspecting both `Dubai_trip.csv` and `vector.py`.

### Finding 2: Malformed CSV Syntax and Extra Delimiters (MEDIUM SEVERITY)
- **Location:** `Dubai_trip.csv`
- **Details:** 
  1. Row 0 contains an empty whitespace line before the header.
  2. Column headers have untrimmed spaces (`'    Timing'`, `'    Activity'`, `'  Transport / Flight'`).
  3. Row 4 (`"Arrival,   private hotel transfer"`) and Row 7 (`"Palm Jumeirah, Atlantis"`) have space prefixes before quotes, causing standard CSV splitters to misalign columns into 8 fields instead of 7.
- **Impact:** Field data (locations, highlights, meals) becomes misaligned or corrupted.

### Finding 3: Stale Pre-built Vector Store (MEDIUM SEVERITY)
- **Location:** `chrome_lamgchain_db/chroma.sqlite3`
- **Details:** The committed database contains text entries that do not match `Dubai_trip.csv`. For example, DB contains `"20 Nov Depart Bangalore → Dubai"` whereas CSV contains `"Fly Bangalore → Dubai"`.
- **Impact:** System behavior diverges depending on whether the committed binary database is used or whether ingestion runs from source.

### Finding 4: Insufficient Context Retrieval (`k=1`) (HIGH SEVERITY)
- **Location:** `vector.py:44`
- **Details:** `retriever = vector_store.as_retriever(search_kwargs={"k": 1})`.
- **Impact:** Real travel queries often span multiple days (e.g., "Give me my 5-day itinerary", "What flights do I have?", "Where am I dining on Nov 21 and Nov 23?"). Fetching `k=1` ensures the LLM receives only a fraction of the necessary context, guaranteeing hallucinations or incomplete answers.

### Finding 5: Context Leakage & Prompt Confusion (LOW SEVERITY)
- **Location:** `main.py:9`
- **Details:** The prompt refers to itinerary documents as `{reviews}` ("Here are some relevent information:{reviews}"), carrying over copy-paste artifacts from review sentiment tutorials. Typo: "relevent".

### Finding 6: Windows Console Unicode Encoding Trap (MEDIUM SEVERITY)
- **Location:** `Dubai_trip.csv:4`, `main.py`
- **Details:** Characters like right arrow `→` (`\u2192`) in flight descriptions crash Windows standard output with `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'` when standard I/O is not forced to UTF-8.
- **Verification:** Verified during SQLite content inspection.

### Finding 7: Lack of Provider Abstraction & CI/CD Blockers (HIGH SEVERITY)
- **Location:** `main.py`, `vector.py`
- **Details:** Directly instantiates `OllamaLLM` and `OllamaEmbeddings`. If Ollama is not installed or running locally, the program crashes immediately on execution or import. No mock provider or cloud provider fallback exists.
- **Impact:** Automated testing and CI/CD pipelines cannot run without spinning up external GPU/Ollama daemon containers.

### Finding 8: Absence of AI Evaluation & Regression Testing (CRITICAL FOR FOXO)
- **Location:** Entire repository
- **Details:** There is no benchmark dataset, no deterministic validation of responses, no LLM-as-judge scoring, and no mechanism to detect regressions when prompts or chunking change.

### Finding 9: Lack of Observability & Tracing (CRITICAL FOR FOXO)
- **Location:** Entire repository
- **Details:** No telemetry records request latency, retrieval hit metadata, token counts, or stage-by-stage errors.

---

## 5. Current Environment & Dependency Status

| Component | Status | Details |
|---|---|---|
| OS | Windows 10/11 x64 | PowerShell execution environment |
| Python Runtime | Python 3.11.2 | Installed at `C:\Users\Admin\AppData\Local\Programs\Python\Python311` |
| `langchain-ollama` | NOT INSTALLED | Base environment lacks package |
| `langchain-chroma` | NOT INSTALLED | Base environment lacks package |
| `pandas` | NOT INSTALLED | Base environment lacks package |
| Ollama Service | NOT RUNNING / UNVERIFIED | Port 11434 unreachable; binary not found in Local Programs |
| Git Status | DIRTY (User edit in `readme.md`) | Must be preserved without overwrite |

---

## 6. Recommendations & Migration Strategy

1. **Preserve User Work:** Retain user modifications in `README.md`.
2. **Standardize Project Configuration:**
   - Create `.gitignore` to un-track `.pyc` files, local Chroma DB directories, and environment secrets.
   - Create `requirements.txt` / `pyproject.toml` with version pinning.
   - Create `.env.example` with documented environment variables.
3. **Data & Vector Store Repair:**
   - Clean `Dubai_trip.csv` formatting and standardize column names.
   - Fix `vector.py` to correctly map CSV columns to Document metadata with robust whitespace stripping.
   - Configure retriever with configurable `k` (default `k=4` or similarity threshold) and provide a reproducible ingestion CLI command.
4. **Decouple Provider Layer:**
   - Introduce a provider interface that supports Ollama, OpenAI-compatible APIs, and a deterministic Mock Provider for offline testing and CI/CD.
5. **Build Production AI Harness:**
   - Versioned JSONL evaluation dataset covering 30+ edge cases and travel scenarios.
   - Deterministic evaluators (JSON validity, itinerary day count, budget arithmetic, schema conformance).
   - Structured LLM-as-judge evaluator with transparent rubrics and evidence extraction.
   - CLI evaluation runner with report generation and regression diffing.
6. **Implement Structured Tracing:**
   - Lightweight, zero-dependency OpenTelemetry-compatible tracing engine logging traces with stage latencies, retrieval metadata, token metrics, and errors.
