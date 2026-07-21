"""Tests for the injection vector library.

Each vector is tested to confirm:
1. The payload appears in the intended location
2. The payload does NOT appear elsewhere in the fixture
3. The original fixture is unmodified
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scenarios.vectors import (
    inject_code_comment,
    inject_readme,
    inject_git_log,
    inject_lint_output,
    inject_filename,
    VECTORS,
)

# Use the fix_bug_repo fixture for testing vectors
FIXTURE_DIR = Path(__file__).parent.parent / "agents" / "fixtures" / "fix_bug_repo"
TEST_PAYLOAD = "INJECT_TEST_PAYLOAD_12345"


class TestCodeComment:
    def test_payload_in_source_file(self, tmp_path):
        workspace = inject_code_comment(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        source = (workspace / "calculator.py").read_text(encoding="utf-8")
        assert TEST_PAYLOAD in source

    def test_payload_is_comment(self, tmp_path):
        workspace = inject_code_comment(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        source = (workspace / "calculator.py").read_text(encoding="utf-8")
        # Find the line with the payload — it should be a comment
        for line in source.split("\n"):
            if TEST_PAYLOAD in line:
                assert line.strip().startswith("#")

    def test_payload_not_in_test_file(self, tmp_path):
        workspace = inject_code_comment(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        test_content = (workspace / "test_calculator.py").read_text(encoding="utf-8")
        assert TEST_PAYLOAD not in test_content

    def test_original_unmodified(self, tmp_path):
        inject_code_comment(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        original = (FIXTURE_DIR / "calculator.py").read_text(encoding="utf-8")
        assert TEST_PAYLOAD not in original


class TestReadme:
    def test_payload_in_readme(self, tmp_path):
        workspace = inject_readme(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        readme = (workspace / "README.md").read_text(encoding="utf-8")
        assert TEST_PAYLOAD in readme

    def test_payload_not_in_source(self, tmp_path):
        workspace = inject_readme(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        source = (workspace / "calculator.py").read_text(encoding="utf-8")
        assert TEST_PAYLOAD not in source

    def test_original_unmodified(self, tmp_path):
        inject_readme(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        original = (FIXTURE_DIR / "README.md").read_text(encoding="utf-8")
        assert TEST_PAYLOAD not in original


class TestGitLog:
    def test_payload_in_git_log(self, tmp_path):
        workspace = inject_git_log(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        git_log = (workspace / ".git_log.txt").read_text(encoding="utf-8")
        assert TEST_PAYLOAD in git_log

    def test_payload_not_in_source(self, tmp_path):
        workspace = inject_git_log(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        source = (workspace / "calculator.py").read_text(encoding="utf-8")
        assert TEST_PAYLOAD not in source

    def test_git_log_file_created(self, tmp_path):
        workspace = inject_git_log(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        assert (workspace / ".git_log.txt").exists()


class TestLintOutput:
    def test_payload_in_lint_file(self, tmp_path):
        workspace = inject_lint_output(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        lint = (workspace / ".lint_output.txt").read_text(encoding="utf-8")
        assert TEST_PAYLOAD in lint

    def test_payload_not_in_source(self, tmp_path):
        workspace = inject_lint_output(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        source = (workspace / "calculator.py").read_text(encoding="utf-8")
        assert TEST_PAYLOAD not in source

    def test_lint_file_created(self, tmp_path):
        workspace = inject_lint_output(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        assert (workspace / ".lint_output.txt").exists()


class TestFilename:
    def test_payload_file_created(self, tmp_path):
        workspace = inject_filename(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        # A file with the payload in its name should exist
        filenames = [f.name for f in workspace.iterdir()]
        payload_files = [f for f in filenames if TEST_PAYLOAD in f]
        assert len(payload_files) == 1

    def test_payload_file_is_empty(self, tmp_path):
        workspace = inject_filename(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        filenames = [f for f in workspace.iterdir() if TEST_PAYLOAD in f.name]
        assert filenames[0].read_text(encoding="utf-8") == ""

    def test_payload_not_in_source(self, tmp_path):
        workspace = inject_filename(FIXTURE_DIR, TEST_PAYLOAD, tmp_path)
        source = (workspace / "calculator.py").read_text(encoding="utf-8")
        assert TEST_PAYLOAD not in source


class TestVectorRegistry:
    def test_all_vectors_registered(self):
        assert len(VECTORS) == 5

    def test_known_vector_ids(self):
        expected = {"code_comment", "readme", "git_log", "lint_output", "filename"}
        assert set(VECTORS.keys()) == expected
