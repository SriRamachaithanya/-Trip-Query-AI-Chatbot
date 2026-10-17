"""
Configuration loader for Trip Query AI Chatbot.
Loads settings from environment variables or .env file with defaults.
"""
import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

@dataclass
class AppConfig:
    workspace_root: Path = WORKSPACE_ROOT
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock").lower()
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
    
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    csv_path: Path = WORKSPACE_ROOT / "Dubai_trip.csv"
    chroma_db_dir: Path = WORKSPACE_ROOT / os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_db")
    retriever_k: int = int(os.getenv("RETRIEVER_K", "4"))
    
    tracing_enabled: bool = os.getenv("TRACING_ENABLED", "true").lower() == "true"
    trace_dir: Path = WORKSPACE_ROOT / os.getenv("TRACE_DIR", "traces")
    eval_reports_dir: Path = WORKSPACE_ROOT / os.getenv("EVAL_REPORTS_DIR", "evals/reports")

config = AppConfig()
