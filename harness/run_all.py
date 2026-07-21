"""Batch execution CLI — runs all scenarios and saves transcripts.

Usage:
    uv run python -m harness.run_all                          # Run all 36 scenarios
    uv run python -m harness.run_all --scenario clean_fix_bug_01  # Run one
    uv run python -m harness.run_all --sandbox docker         # Use Docker sandbox
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

# Default directories
CASES_DIR = Path(__file__).parent.parent / "scenarios" / "cases"
REPORTS_DIR = Path(__file__).parent.parent / "reports" / "runs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_scenarios(
    cases_dir: Path, scenario_id: str | None = None
) -> list[Scenario]:
    """Load scenario definitions from YAML files.

    Args:
        cases_dir: Directory containing scenario YAML files.
        scenario_id: If provided, load only this specific scenario.

    Returns:
        List of Scenario objects.
    """
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
    """Save a RunResult as JSON.

    Args:
        result: The run result to save.
        output_dir: Directory to write the JSON file to.

    Returns:
        Path to the saved file.
    """
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
) -> list[RunResult]:
    """Run all (or one) scenario and save results.

    Args:
        cases_dir: Directory containing scenario YAML files.
        output_dir: Directory to save result JSON files.
        sandbox: Sandbox mode — "process" or "docker".
        scenario_id: If provided, run only this specific scenario.

    Returns:
        List of RunResult objects.
    """
    scenarios = load_scenarios(cases_dir, scenario_id)
    if not scenarios:
        logger.error("No scenarios to run")
        return []

    agent = ToyAgent()
    runner = ScenarioRunner(agent=agent, sandbox=sandbox)

    results: list[RunResult] = []
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

        # Save immediately so partial runs are preserved
        save_path = save_result(result, output_dir)

        status = "✅" if result.task_success else "❌"
        leak = ""
        if result.canary_leaked is not None:
            leak = " | 🔓 LEAKED" if result.canary_leaked else " | 🔒 safe"
        error = f" | ⚠️ ERROR: {result.error}" if result.error else ""

        print(f"         {status} task={result.task_success}{leak}{error}")
        print(f"         ⏱️ {result.duration_seconds:.1f}s → {save_path.name}")
        print()

    # Print summary
    _print_summary(results)
    return results


def _print_summary(results: list[RunResult]) -> None:
    """Print a summary table of the run."""
    total = len(results)
    clean = [r for r in results if r.scenario.is_clean]
    attacked = [r for r in results if not r.scenario.is_clean]

    clean_success = sum(1 for r in clean if r.task_success)
    attack_success = sum(1 for r in attacked if r.task_success)
    canary_leaks = sum(1 for r in results if r.canary_leaked)
    errors = sum(1 for r in results if r.error)

    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total scenarios:     {total}")
    print(f"  Clean runs:          {len(clean)} (task success: {clean_success}/{len(clean)})")
    print(f"  Attacked runs:       {len(attacked)} (task success: {attack_success}/{len(attacked)})")
    print(f"  Canary leaks:        {canary_leaks}")
    print(f"  Errors:              {errors}")
    print(f"{'=' * 60}\n")


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
    args = parser.parse_args()

    results = run_all(
        cases_dir=Path(args.cases_dir),
        output_dir=Path(args.output_dir),
        sandbox=args.sandbox,
        scenario_id=args.scenario,
    )

    # Exit with non-zero if any scenario had errors
    if any(r.error for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
