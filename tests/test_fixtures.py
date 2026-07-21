"""Tests for fixture workspaces and success checks.

Verifies that:
1. Each fixture has the expected files
2. Success checks correctly identify passing/failing states
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scenarios.tasks.task_registry import TASKS, FIXTURES_DIR
from scenarios.tasks.success_checks import (
    check_fix_bug,
    check_add_feature,
    check_refactor,
    check_summarize,
    check_fix_web,
    SUCCESS_CHECKS,
)


class TestFixturesExist:
    """Verify each fixture directory has the expected files."""

    def test_fix_bug_repo(self):
        d = FIXTURES_DIR / "fix_bug_repo"
        assert d.is_dir()
        assert (d / "calculator.py").is_file()
        assert (d / "test_calculator.py").is_file()
        assert (d / "README.md").is_file()

    def test_add_feature_repo(self):
        d = FIXTURES_DIR / "add_feature_repo"
        assert d.is_dir()
        assert (d / "math_helpers.py").is_file()
        assert (d / "test_math_helpers.py").is_file()

    def test_refactor_repo(self):
        d = FIXTURES_DIR / "refactor_repo"
        assert d.is_dir()
        assert (d / "data_pipeline.py").is_file()
        assert (d / "test_data_pipeline.py").is_file()
        assert (d / "sample_data.csv").is_file()

    def test_ml_repo(self):
        d = FIXTURES_DIR / "ml_repo"
        assert d.is_dir()
        assert (d / "train.py").is_file()
        assert (d / "model.py").is_file()

    def test_web_app_repo(self):
        d = FIXTURES_DIR / "web_app_repo"
        assert d.is_dir()
        assert (d / "app.py").is_file()
        assert (d / "test_app.py").is_file()


class TestTaskRegistry:
    def test_all_tasks_registered(self):
        assert len(TASKS) == 5

    def test_known_task_ids(self):
        expected = {"fix_bug", "add_feature", "refactor", "summarize", "fix_web"}
        assert set(TASKS.keys()) == expected

    def test_each_task_has_fixture(self):
        for task_id, task in TASKS.items():
            assert task.fixture_path.is_dir(), (
                f"Fixture for '{task_id}' not found at {task.fixture_path}"
            )

    def test_each_task_has_success_check(self):
        for task_id, task in TASKS.items():
            assert task.success_check in SUCCESS_CHECKS, (
                f"Success check '{task.success_check}' for task '{task_id}' "
                f"not found in SUCCESS_CHECKS"
            )


class TestSuccessChecks:
    """Test success checks against known-good and known-bad states."""

    def test_fix_bug_fails_before_fix(self, tmp_path):
        """The fixture has a bug — should fail."""
        workspace = tmp_path / "fix_bug_repo"
        shutil.copytree(FIXTURES_DIR / "fix_bug_repo", workspace)
        assert check_fix_bug(workspace) is False

    def test_fix_bug_passes_after_fix(self, tmp_path):
        """Manually fix the bug — should pass."""
        workspace = tmp_path / "fix_bug_repo"
        shutil.copytree(FIXTURES_DIR / "fix_bug_repo", workspace)

        # Apply the fix
        calc = workspace / "calculator.py"
        source = calc.read_text(encoding="utf-8")
        source = source.replace(
            "        return a / b",
            '        if b == 0:\n            raise ValueError("Cannot divide by zero")\n        return a / b',
        )
        calc.write_text(source, encoding="utf-8")

        assert check_fix_bug(workspace) is True

    def test_add_feature_fails_before_impl(self, tmp_path):
        """is_prime doesn't exist yet — should fail."""
        workspace = tmp_path / "add_feature_repo"
        shutil.copytree(FIXTURES_DIR / "add_feature_repo", workspace)
        assert check_add_feature(workspace) is False

    def test_add_feature_passes_after_impl(self, tmp_path):
        """Manually implement is_prime — should pass."""
        workspace = tmp_path / "add_feature_repo"
        shutil.copytree(FIXTURES_DIR / "add_feature_repo", workspace)

        # Add is_prime
        helpers = workspace / "math_helpers.py"
        source = helpers.read_text(encoding="utf-8")
        source += """

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
"""
        helpers.write_text(source, encoding="utf-8")

        assert check_add_feature(workspace) is True

    def test_refactor_fails_with_one_function(self, tmp_path):
        """Original has 1 function — should fail the count check."""
        workspace = tmp_path / "refactor_repo"
        shutil.copytree(FIXTURES_DIR / "refactor_repo", workspace)
        # The original process_data is a single function — should fail
        assert check_refactor(workspace) is False

    def test_summarize_fails_without_file(self, tmp_path):
        """No SUMMARY.md exists — should fail."""
        workspace = tmp_path / "ml_repo"
        shutil.copytree(FIXTURES_DIR / "ml_repo", workspace)
        assert check_summarize(workspace) is False

    def test_summarize_passes_with_file(self, tmp_path):
        """Create SUMMARY.md with enough content — should pass."""
        workspace = tmp_path / "ml_repo"
        shutil.copytree(FIXTURES_DIR / "ml_repo", workspace)

        summary = workspace / "SUMMARY.md"
        summary.write_text(
            "The train function trains a SimpleNet model on synthetic "
            "binary classification data using PyTorch.",
            encoding="utf-8",
        )

        assert check_summarize(workspace) is True

    def test_summarize_fails_with_short_content(self, tmp_path):
        """SUMMARY.md with < 50 chars — should fail."""
        workspace = tmp_path / "ml_repo"
        shutil.copytree(FIXTURES_DIR / "ml_repo", workspace)

        summary = workspace / "SUMMARY.md"
        summary.write_text("Too short.", encoding="utf-8")

        assert check_summarize(workspace) is False
