"""Tests for Docker sandbox.

These tests require Docker to be installed and running. They are marked
with @pytest.mark.docker and are excluded from the default test run.

Run with: uv run pytest tests/test_docker_sandbox.py -m docker -v
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from harness.sandbox import DockerSandbox, DOCKER_IMAGE, PROJECT_ROOT


pytestmark = pytest.mark.docker


def _docker_available() -> bool:
    """Check if Docker is installed and the daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


if not _docker_available():
    pytest.skip("Docker is not available", allow_module_level=True)


class TestDockerSandboxBuild:
    def test_dockerfile_exists(self):
        """The Dockerfile should exist at the project root."""
        assert (PROJECT_ROOT / "Dockerfile").is_file()

    def test_dockerignore_exists(self):
        """The .dockerignore should exist at the project root."""
        assert (PROJECT_ROOT / ".dockerignore").is_file()

    def test_image_builds_successfully(self):
        """The Docker image should build without errors."""
        result = subprocess.run(
            ["docker", "build", "-t", DOCKER_IMAGE, str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, (
            f"Docker build failed:\nstdout: {result.stdout[-500:]}\n"
            f"stderr: {result.stderr[-500:]}"
        )

    def test_image_has_python(self):
        """The built image should have Python available."""
        result = subprocess.run(
            ["docker", "run", "--rm", DOCKER_IMAGE, "python", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Python 3.12" in result.stdout


class TestDockerSandboxPrepare:
    def test_prepare_workspace_creates_temp_dir(self, tmp_path):
        """prepare_workspace should copy fixture contents to a temp dir."""
        # Create a small fake fixture
        fixture = tmp_path / "fake_fixture"
        fixture.mkdir()
        (fixture / "test.py").write_text("print('hello')", encoding="utf-8")

        sandbox = DockerSandbox(auto_build=False)
        sandbox._image_built = True  # Skip image check

        workspace = sandbox.prepare_workspace(fixture)
        try:
            assert workspace.is_dir()
            assert (workspace / "test.py").is_file()
            assert workspace != fixture  # Must be a copy
        finally:
            sandbox.cleanup(workspace)
