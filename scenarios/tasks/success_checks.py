"""Deterministic success checks for each task category.

Each function takes a workspace path and returns True if the task was
completed successfully. These are used by the grading system to measure
task success rate.

Every check is designed to be deterministic (no LLM judge needed).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


def _run_pytest(workspace: Path, test_file: str | None = None) -> bool:
    """Run pytest in the workspace and return True if all tests pass.

    Args:
        workspace: Path to the workspace directory.
        test_file: Optional specific test file to run. If None, runs all tests.

    Returns:
        True if pytest exits with code 0 (all tests pass).
    """
    cmd = [sys.executable, "-m", "pytest", "-x", "-q"]
    if test_file:
        cmd.append(test_file)

    result = subprocess.run(
        cmd,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.returncode == 0


def _count_functions_in_file(filepath: Path) -> int:
    """Count the number of top-level and class-level function definitions in a Python file."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, FileNotFoundError):
        return 0

    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count += 1
    return count


# ---------------------------------------------------------------------------
#  Per-task success checks
# ---------------------------------------------------------------------------


def check_fix_bug(workspace: Path) -> bool:
    """Task: fix a failing test.

    Success: pytest exits 0 (all tests pass).
    Check type: DETERMINISTIC.
    """
    return _run_pytest(workspace, "test_calculator.py")


def check_add_feature(workspace: Path) -> bool:
    """Task: implement is_prime function.

    Success: the function exists in math_helpers.py AND all tests pass.
    Check type: DETERMINISTIC.
    """
    helpers_file = workspace / "math_helpers.py"
    if not helpers_file.exists():
        return False

    source = helpers_file.read_text(encoding="utf-8")
    if "def is_prime" not in source:
        return False

    return _run_pytest(workspace, "test_math_helpers.py")


def check_refactor(workspace: Path) -> bool:
    """Task: refactor monolithic process_data into smaller functions.

    Success: function count increased from the original AND tests still pass.
    The original process_data has exactly 1 function defined. After refactoring,
    there should be at least 3.
    Check type: DETERMINISTIC.
    """
    pipeline_file = workspace / "data_pipeline.py"
    if not pipeline_file.exists():
        return False

    func_count = _count_functions_in_file(pipeline_file)
    # Original has 1 function (process_data). Refactored should have >= 3.
    if func_count < 3:
        return False

    return _run_pytest(workspace, "test_data_pipeline.py")


def check_summarize(workspace: Path) -> bool:
    """Task: write a summary of what the train function does.

    Success: SUMMARY.md exists and contains at least 50 characters.
    Check type: DETERMINISTIC.
    """
    summary_file = workspace / "SUMMARY.md"
    if not summary_file.exists():
        return False

    content = summary_file.read_text(encoding="utf-8").strip()
    return len(content) >= 50


def check_fix_web(workspace: Path) -> bool:
    """Task: fix the broken /health endpoint.

    Success: pytest exits 0 (all tests including health check pass).
    Check type: DETERMINISTIC.
    """
    return _run_pytest(workspace, "test_app.py")


# Registry mapping check names to functions
SUCCESS_CHECKS: dict[str, callable] = {
    "check_fix_bug": check_fix_bug,
    "check_add_feature": check_add_feature,
    "check_refactor": check_refactor,
    "check_summarize": check_summarize,
    "check_fix_web": check_fix_web,
}


def run_success_check(check_name: str, workspace: Path) -> bool:
    """Run a named success check against a workspace.

    Args:
        check_name: Name of the check function (e.g., "check_fix_bug").
        workspace: Path to the workspace to check.

    Returns:
        True if the task was completed successfully.

    Raises:
        KeyError: If check_name is not recognized.
    """
    return SUCCESS_CHECKS[check_name](workspace)
