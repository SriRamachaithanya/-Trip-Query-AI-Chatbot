"""
Command-Line Evaluation Runner for Trip Query AI Chatbot.
Executes test cases, computes deterministic and judge metrics, generates JSON reports,
and compares results against baseline evaluation runs.
"""
import os
import sys

# Ensure UTF-8 output handling on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import time
import argparse
import glob
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.core.pipeline import TripRAGPipeline
from src.core.config import config
from src.providers import get_provider
from src.evals.schemas import EvalCase, CaseResult, EvalRunReport
from src.evals.deterministic import evaluate_deterministic
from src.evals.judge import LLMJudgeEvaluator

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

def load_dataset(dataset_path: Path) -> List[EvalCase]:
    """Loads and validates test cases from a JSONL file."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at: {dataset_path}")

    cases = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                case = EvalCase(
                    id=data["id"],
                    dataset_version=data.get("dataset_version", "v1.0"),
                    difficulty=data.get("difficulty", "medium"),
                    tags=data.get("tags", []),
                    input=data["input"],
                    expected_behavior=data["expected_behavior"],
                    evaluation_criteria=data.get("evaluation_criteria", {})
                )
                cases.append(case)
            except Exception as e:
                print(f"[WARNING] Skipping invalid dataset line {line_num}: {e}")

    return cases

def run_evaluation(
    dataset_path: str = "evals/datasets/v1.jsonl",
    provider_name: str = "mock",
    enable_judge: bool = False,
    save_report: bool = True,
    compare_baseline: Optional[str] = None
) -> EvalRunReport:
    """Runs the full evaluation benchmark suite."""
    dataset_file = Path(dataset_path)
    cases = load_dataset(dataset_file)
    print("\n" + "="*60)
    print(">> Starting Trip Query AI Evaluation Suite")
    print(f"Dataset: {dataset_file.name} ({len(cases)} cases) | Provider: {provider_name.upper()} | Judge: {'ON' if enable_judge else 'OFF'}")
    print("="*60 + "\n")

    provider = get_provider(
        provider_type=provider_name,
        ollama_base_url=config.ollama_base_url,
        ollama_model=config.ollama_model,
        openai_api_key=config.openai_api_key,
        openai_base_url=config.openai_base_url,
        openai_model=config.openai_model
    )
    pipeline = TripRAGPipeline(provider=provider, retriever_k=config.retriever_k)
    judge = LLMJudgeEvaluator(provider=provider) if enable_judge else None

    run_id = f"eval_{int(time.time())}"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    case_results: List[CaseResult] = []
    total_latency = 0.0

    for idx, case in enumerate(cases, 1):
        print(f"[{idx:02d}/{len(cases):02d}] Evaluating {case.id} ... ", end="", flush=True)
        
        # Execute RAG query
        response = pipeline.run(case.input)
        total_latency += response.latency_ms

        # Run deterministic checks
        det_checks = evaluate_deterministic(case, response)
        failed_checks = [c for c in det_checks if not c.passed]
        passed = len(failed_checks) == 0
        failure_reasons = [f"{c.check_name}: {c.message}" for c in failed_checks]

        # Run judge if enabled
        judge_score = judge.evaluate(case, response) if judge else None

        result = CaseResult(
            case_id=case.id,
            input=case.input,
            output=response.answer,
            latency_ms=response.latency_ms,
            passed=passed,
            failure_reasons=failure_reasons,
            deterministic_checks=det_checks,
            judge_score=judge_score,
            trace_id=response.trace_id,
            status=response.status
        )
        case_results.append(result)

        if passed:
            print(f"[PASS] ({response.latency_ms}ms)")
        else:
            print(f"[FAIL] ({response.latency_ms}ms) -> {failure_reasons[0]}")

    passed_count = sum(1 for r in case_results if r.passed)
    failed_count = len(case_results) - passed_count
    pass_rate = round((passed_count / len(case_results)) * 100, 1) if case_results else 0.0
    avg_lat = round(total_latency / len(case_results), 1) if case_results else 0.0

    # Judge summary
    judge_summary = {}
    if enable_judge:
        avg_judge = round(sum(r.judge_score.overall_score for r in case_results if r.judge_score) / len(case_results), 2)
        judge_summary = {
            "avg_overall_score": avg_judge,
            "rubric_version": "v1.2"
        }

    # Baseline comparison
    comparison_data = None
    if compare_baseline:
        comparison_data = compare_with_previous(compare_baseline, pass_rate, avg_lat)

    report = EvalRunReport(
        run_id=run_id,
        timestamp=timestamp,
        dataset_path=str(dataset_file),
        total_cases=len(case_results),
        passed_cases=passed_count,
        failed_cases=failed_count,
        pass_rate_pct=pass_rate,
        avg_latency_ms=avg_lat,
        results=case_results,
        judge_enabled=enable_judge,
        judge_summary=judge_summary,
        comparison=comparison_data
    )

    # Save report
    if save_report:
        report_dir = Path("evals/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"{run_id}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n[REPORT] Detailed machine-readable report saved to: {report_file}")

    print_terminal_summary(report)
    return report

def compare_with_previous(baseline_arg: str, current_pass_rate: float, current_avg_lat: float) -> Dict[str, Any]:
    """Compares current run metrics with a previous report file or latest report."""
    baseline_path = None
    if baseline_arg == "latest" or baseline_arg is True:
        existing_reports = sorted(glob.glob("evals/reports/eval_*.json"))
        if existing_reports:
            baseline_path = existing_reports[-1]
    elif Path(baseline_arg).exists():
        baseline_path = baseline_arg

    if not baseline_path:
        return {"note": "No valid previous baseline report found for comparison."}

    try:
        with open(baseline_path, "r", encoding="utf-8") as f:
            prev = json.load(f)
        prev_pass_rate = prev.get("pass_rate_pct", 0.0)
        prev_lat = prev.get("avg_latency_ms", 0.0)
        return {
            "baseline_report": str(baseline_path),
            "prev_pass_rate_pct": prev_pass_rate,
            "pass_rate_diff_pct": round(current_pass_rate - prev_pass_rate, 1),
            "prev_avg_latency_ms": prev_lat,
            "latency_diff_ms": round(current_avg_lat - prev_lat, 1)
        }
    except Exception as e:
        return {"error": f"Failed to compare baseline: {e}"}

def print_terminal_summary(report: EvalRunReport):
    """Outputs a clean summary table to the console."""
    print("\n" + "="*60)
    print("EVALUATION RUN SUMMARY")
    print("="*60)
    summary_table = [
        ["Total Test Cases", report.total_cases],
        ["Passed Cases", f"[PASS] {report.passed_cases}"],
        ["Failed Cases", f"[FAIL] {report.failed_cases}"],
        ["Pass Rate", f"{report.pass_rate_pct}%"],
        ["Average Latency", f"{report.avg_latency_ms} ms"],
        ["Judge Evaluator", "Enabled" if report.judge_enabled else "Disabled"]
    ]
    if report.judge_enabled and report.judge_summary:
        summary_table.append(["Judge Avg Score", f"{report.judge_summary.get('avg_overall_score')}/5.0"])

    if report.comparison and "prev_pass_rate_pct" in report.comparison:
        diff = report.comparison.get("pass_rate_diff_pct", 0.0)
        diff_str = f"+{diff}%" if diff >= 0 else f"{diff}%"
        summary_table.append(["Baseline Comparison", f"Diff: {diff_str} (prev: {report.comparison.get('prev_pass_rate_pct')}%)"])

    if HAS_TABULATE:
        print(tabulate(summary_table, headers=["Metric", "Value"], tablefmt="grid"))
    else:
        for row in summary_table:
            print(f"  * {row[0]}: {row[1]}")
    print("="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Trip Query AI Evaluation Harness Runner")
    parser.add_argument("--dataset", type=str, default="evals/datasets/v1.jsonl", help="Path to evaluation dataset")
    parser.add_argument("--provider", type=str, default="mock", choices=["mock", "ollama", "openai"], help="Model provider")
    parser.add_argument("--enable-judge", action="store_true", help="Enable qualitative LLM judge scoring")
    parser.add_argument("--compare-baseline", type=str, default=None, help="Path to previous report or 'latest'")
    parser.add_argument("--no-save", action="store_true", help="Do not save JSON report to disk")

    args = parser.parse_args()
    report = run_evaluation(
        dataset_path=args.dataset,
        provider_name=args.provider,
        enable_judge=args.enable_judge,
        save_report=not args.no_save,
        compare_baseline=args.compare_baseline
    )

    if report.failed_cases > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
