# Baseline Report & Project State

**Project:** Trip Query AI Chatbot  
**Target Goal:** Production-Grade AI Engineering Upgrade (FOXO AI Selection)  
**Baseline Date:** October 17, 2026  
**Status:** Baseline Established & Documented  

---

## 1. Initial State Summary & Blockers

Prior to this upgrade, running the application in a fresh environment failed immediately due to several critical blockers:

1. **Unmet Runtime Dependencies in Host Environment:**
   - Packages `langchain-ollama`, `langchain-chroma`, and `pandas` were absent from the global Python 3.11 environment.
   - Command `python vector.py` crashed with:
     ```
     ModuleNotFoundError: No module named 'langchain_ollama'
     ```
2. **Missing Local Ollama Service:**
   - The application relies on `OllamaLLM(model="llama3.2")` and `OllamaEmbeddings(model="mxbai-embed-large")`.
   - The local Ollama server (`http://localhost:11434`) was inactive/unreachable.
3. **Data Schema Crash in `vector.py`:**
   - Line 25 in `vector.py` queried `row["Attractions / Details"]`.
   - `Dubai_trip.csv` header contained `Highlights`. If the database were to be recreated from scratch, execution failed with `KeyError: 'Attractions / Details'`.
4. **Malformed CSV Quotes:**
   - Raw lines with spaces before quotes (`"Arrival,   private hotel transfer"`) caused delimiter splits into 8 fields instead of 7.
5. **Windows cp1252 Unicode Trap:**
   - Flight arrow symbol (`→`) threw `UnicodeEncodeError: 'charmap'` when written to stdout under default Windows console encoding.

---

## 2. Baseline Remediation & Setup Instructions

To establish a reproducible and isolated development baseline:

### Step 1: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Minimal Testing & Validation Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
```powershell
Copy-Item .env.example .env
# Adjust LLM_PROVIDER to 'mock', 'ollama', or 'openai'
```

---

## 3. Baseline Smoke Test Results

A set of automated smoke tests (`tests/test_baseline.py`) was introduced to verify hygiene, CSV normalization, syntax validity, and configuration without requiring external GPU or daemon services.

**Command Executed:**
```powershell
.\.venv\Scripts\pytest tests/test_baseline.py -v
```

**Results:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.2, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Admin\Desktop\projects\-Trip-Query-AI-Chatbot
configfile: pyproject.toml
collected 4 items

tests/test_baseline.py::test_dubai_trip_csv_integrity PASSED             [ 25%]
tests/test_baseline.py::test_env_example_contains_all_placeholders PASSED [ 50%]
tests/test_baseline.py::test_gitignore_covers_sensitive_and_binary_files PASSED [ 75%]
tests/test_baseline.py::test_python_source_syntax_validity PASSED        [100%]

============================== 4 passed in 0.03s ==============================
```

---

## 4. Known Limitations & Target Evolution

1. **Retrieval Depth (`k=1`):** Baseline retrieval retrieves only a single row, omitting multi-day context. Target architecture expands to `k=4` with metadata fusion.
2. **Provider Lock-In:** Baseline is hardcoded to Ollama. Target architecture introduces a Provider Abstraction Layer supporting `MockProvider` (for deterministic CI/evals), `OllamaProvider`, and `OpenAIProvider`.
3. **Observability Absence:** Zero logging or tracing in baseline. Target architecture integrates `src/tracing/` to track stage latencies, token consumption, and errors.
4. **Evaluation Absence:** No objective metrics or regression guards exist. Phase 3 introduces a 30+ scenario versioned evaluation dataset and multi-metric evaluators.
