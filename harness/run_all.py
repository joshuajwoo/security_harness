"""Batch execution CLI — runs all scenarios and saves transcripts.

Usage:
    uv run python -m harness.run_all                          # Run all 36 scenarios
    uv run python -m harness.run_all --scenario clean_fix_bug_01  # Run one
    uv run python -m harness.run_all --sandbox docker         # Use Docker sandbox
    uv run python -m harness.run_all --report                 # Generate markdown report
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

from agents.toy_agent import ToyAgent
from harness.models import RunResult
from harness.runner import ScenarioRunner
from scenarios.schema import Scenario

from harness.grading.rules import run_security_checks
from harness.grading.task_success import grade_task_success
from harness.grading.containment import classify_containment
from harness.grading.aggregate import GradedResult, aggregate_metrics, print_metrics
from harness.report import generate_markdown_report

# Default directories
CASES_DIR = Path(__file__).parent.parent / "scenarios" / "cases"
REPORTS_DIR = Path(__file__).parent.parent / "reports" / "runs"
REPORT_OUTPUT_FILE = Path(__file__).parent.parent / "reports" / "report.md"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_scenarios(
    cases_dir: Path, scenario_id: str | None = None
) -> list[Scenario]:
    scenarios = []
    yaml_files = sorted(cases_dir.glob("*.yaml"))

    for filepath in yaml_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        scenario = Scenario(**data)

        if scenario_id and scenario.scenario_id != scenario_id:
            continue

        scenarios.append(scenario)

    if scenario_id and not scenarios:
        logger.error("Scenario '%s' not found in %s", scenario_id, cases_dir)

    return scenarios


def save_result(result: RunResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{result.scenario.scenario_id}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    return filepath


def run_all(
    cases_dir: Path = CASES_DIR,
    output_dir: Path = REPORTS_DIR,
    sandbox: str = "process",
    scenario_id: str | None = None,
    generate_report: bool = False,
) -> tuple[list[RunResult], list[GradedResult]]:
    scenarios = load_scenarios(cases_dir, scenario_id)
    if not scenarios:
        logger.error("No scenarios to run")
        return [], []

    agent = ToyAgent()
    runner = ScenarioRunner(agent=agent, sandbox=sandbox)

    results: list[RunResult] = []
    graded_results: list[GradedResult] = []
    total = len(scenarios)

    print(f"\n{'=' * 60}")
    print(f"  Security Harness — Running {total} scenario(s)")
    print(f"  Sandbox: {sandbox}")
    print(f"{'=' * 60}\n")

    for i, scenario in enumerate(scenarios, 1):
        tag = "CLEAN" if scenario.is_clean else "ATTACK"
        print(f"[{i}/{total}] {tag} | {scenario.scenario_id}")

        result = runner.run(scenario)
        results.append(result)

        # Save raw run result
        save_path = save_result(result, output_dir)

        # Grade the result
        sec_verdict = run_security_checks(result)
        task_grade = grade_task_success(result)
        
        containment = None
        if not scenario.is_clean:
            containment = classify_containment(result.transcript, sec_verdict)
            
        graded = GradedResult(
            scenario_id=scenario.scenario_id,
            task_id=scenario.task_id,
            is_clean=scenario.is_clean,
            vector_id=scenario.vector_id,
            objective_id=scenario.objective_id,
            security_verdict=sec_verdict,
            task_grade=task_grade,
            containment=containment,
            transcript=result.transcript,
        )
        graded_results.append(graded)

        status = "✅" if result.task_success else "❌"
        leak = ""
        if result.canary_leaked is not None:
            leak = " | 🔓 LEAKED" if result.canary_leaked else " | 🔒 safe"
        error = f" | ⚠️ ERROR: {result.error}" if result.error else ""

        print(f"         {status} task={result.task_success}{leak}{error}")
        print(f"         ⏱️ {result.duration_seconds:.1f}s → {save_path.name}")
        print()

    # Aggregate and print metrics
    metrics = aggregate_metrics(graded_results)
    print_metrics(metrics)
    
    if generate_report:
        report_path = generate_markdown_report(metrics, graded_results, REPORT_OUTPUT_FILE)
        print(f"\nReport generated at: {report_path}")

    return results, graded_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run security harness scenarios"
    )
    parser.add_argument(
        "--sandbox",
        default="process",
        choices=["process", "docker"],
        help="Sandbox mode (default: process)",
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help="Run a specific scenario by ID",
    )
    parser.add_argument(
        "--cases-dir",
        default=str(CASES_DIR),
        help="Directory containing scenario YAML files",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPORTS_DIR),
        help="Directory to save result JSON files",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a markdown report after running",
    )
    args = parser.parse_args()

    results, graded_results = run_all(
        cases_dir=Path(args.cases_dir),
        output_dir=Path(args.output_dir),
        sandbox=args.sandbox,
        scenario_id=args.scenario,
        generate_report=args.report,
    )

    # Exit with non-zero if any scenario had errors
    if any(r.error for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
