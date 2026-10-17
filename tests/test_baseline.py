"""
Baseline Smoke Tests for Trip Query AI Chatbot.
Verifies project hygiene, dataset integrity, and environment configuration.
"""
import csv
import os
import ast
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def test_dubai_trip_csv_integrity():
    """Verify that Dubai_trip.csv exists, has valid headers, and parses 9 rows without error."""
    csv_path = WORKSPACE_ROOT / "Dubai_trip.csv"
    assert csv_path.exists(), "Dubai_trip.csv must exist in workspace root"
    
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    
    assert len(reader) == 9, f"Expected 9 itinerary entries, found {len(reader)}"
    expected_headers = {"Date", "Timing", "Activity", "Transport / Flight", "Location", "Highlights", "Meals / Hotel"}
    actual_headers = set(reader[0].keys())
    assert expected_headers.issubset(actual_headers), f"Missing headers: {expected_headers - actual_headers}"
    
    # Verify flight entries
    assert any("EK565" in row["Transport / Flight"] for row in reader), "Arrival flight EK565 not found"
    assert any("EK566" in row["Meals / Hotel"] for row in reader), "Departure flight EK566 not found"

def test_env_example_contains_all_placeholders():
    """Verify .env.example exists and contains standard configuration keys without real secrets."""
    env_example_path = WORKSPACE_ROOT / ".env.example"
    assert env_example_path.exists(), ".env.example must exist"
    
    content = env_example_path.read_text(encoding="utf-8")
    assert "LLM_PROVIDER=" in content
    assert "OLLAMA_BASE_URL=" in content
    assert "OPENAI_API_KEY=" in content
    assert "RETRIEVER_K=" in content
    # Guarantee no real OpenAI key is committed
    assert "sk-" not in content, "Real API key detected in .env.example!"

def test_gitignore_covers_sensitive_and_binary_files():
    """Verify .gitignore properly protects binary caches, databases, and secrets."""
    gitignore_path = WORKSPACE_ROOT / ".gitignore"
    assert gitignore_path.exists(), ".gitignore must exist"
    
    content = gitignore_path.read_text(encoding="utf-8")
    assert "__pycache__" in content
    assert ".venv" in content
    assert ".env" in content
    assert "chrome_lamgchain_db" in content or "*.sqlite3" in content

def test_python_source_syntax_validity():
    """Verify that main.py and vector.py are syntactically valid Python without importing heavy external deps."""
    for script_name in ["main.py", "vector.py"]:
        script_path = WORKSPACE_ROOT / script_name
        assert script_path.exists(), f"{script_name} must exist"
        source = script_path.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as e:
            assert False, f"Syntax error in {script_name}: {e}"
