"""Sandbox implementations for isolated agent execution.

Two sandbox levels:
- ProcessSandbox: copies fixture to a temp dir, relies on agent-level path
  validation. Fast, good for development.
- DockerSandbox: runs the agent inside a Docker container with no network
  access, memory/CPU limits, and a volume-mounted workspace. Secure.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Protocol, runtime_checkable

from agents.adapter import AgentTranscript, TargetAgent

logger = logging.getLogger(__name__)

# Docker image name
DOCKER_IMAGE = "security-harness-sandbox"
# Project root (for building the Docker image)
PROJECT_ROOT = Path(__file__).parent.parent


@runtime_checkable
class Sandbox(Protocol):
    """Protocol for sandbox implementations."""

    def prepare_workspace(self, fixture_dir: Path) -> Path:
        """Copy the fixture to an isolated workspace. Returns the workspace path."""
        ...

    def execute(
        self, agent: TargetAgent, task: str, workspace: Path
    ) -> AgentTranscript:
        """Run the agent on the task inside the sandbox."""
        ...

    def cleanup(self, workspace: Path) -> None:
        """Clean up the sandbox environment."""
        ...


class ProcessSandbox:
    """Process-level sandbox — copies fixture to temp dir.

    Relies on agent-level path validation (the ToyAgent already restricts
    file operations to the workspace directory). No network isolation.

    Good for fast iteration during development.
    """

    def __init__(self, base_dir: Path | None = None):
        """
        Args:
            base_dir: Optional base directory for temp workspaces.
                If None, uses the system temp directory.
        """
        self._base_dir = base_dir

    def prepare_workspace(self, fixture_dir: Path) -> Path:
        """Copy fixture to a new temp directory."""
        if self._base_dir:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            workspace = Path(tempfile.mkdtemp(dir=str(self._base_dir)))
        else:
            workspace = Path(tempfile.mkdtemp(prefix="harness_"))

        # Copy fixture contents into the workspace
        shutil.copytree(fixture_dir, workspace, dirs_exist_ok=True)
        logger.info("ProcessSandbox: prepared workspace at %s", workspace)
        return workspace

    def execute(
        self, agent: TargetAgent, task: str, workspace: Path
    ) -> AgentTranscript:
        """Run the agent directly in this process."""
        return agent.run(task, workspace)

    def cleanup(self, workspace: Path) -> None:
        """Remove the temp directory."""
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
            logger.info("ProcessSandbox: cleaned up %s", workspace)


class DockerSandbox:
    """Docker-based sandbox — runs agent in an isolated container.

    Security guarantees:
    - No network access (--network=none)
    - Memory and CPU limits
    - Only the workspace directory is mounted
    - API key is passed as env var, never written to disk
    - Automatic timeout
    """

    def __init__(
        self,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
        timeout_seconds: int = 120,
        auto_build: bool = True,
    ):
        """
        Args:
            memory_limit: Docker memory limit (e.g., "512m", "1g").
            cpu_limit: Number of CPUs to allocate.
            timeout_seconds: Maximum run time before killing the container.
            auto_build: If True, automatically build the Docker image if
                it doesn't exist.
        """
        self._memory_limit = memory_limit
        self._cpu_limit = cpu_limit
        self._timeout_seconds = timeout_seconds
        self._auto_build = auto_build
        self._image_built = False

    def _ensure_image(self) -> None:
        """Build the Docker image if it doesn't exist."""
        if self._image_built:
            return

        # Check if image already exists
        result = subprocess.run(
            ["docker", "image", "inspect", DOCKER_IMAGE],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            self._image_built = True
            logger.info("DockerSandbox: image '%s' already exists", DOCKER_IMAGE)
            return

        if not self._auto_build:
            raise RuntimeError(
                f"Docker image '{DOCKER_IMAGE}' not found and auto_build=False. "
                f"Build it with: docker build -t {DOCKER_IMAGE} {PROJECT_ROOT}"
            )

        logger.info("DockerSandbox: building image '%s'...", DOCKER_IMAGE)
        result = subprocess.run(
            ["docker", "build", "-t", DOCKER_IMAGE, str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Docker build failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

        self._image_built = True
        logger.info("DockerSandbox: image built successfully")

    def prepare_workspace(self, fixture_dir: Path) -> Path:
        """Copy fixture to a new temp directory on the host."""
        self._ensure_image()

        workspace = Path(tempfile.mkdtemp(prefix="harness_docker_"))
        shutil.copytree(fixture_dir, workspace, dirs_exist_ok=True)
        logger.info("DockerSandbox: prepared workspace at %s", workspace)
        return workspace

    def execute(
        self, agent: TargetAgent, task: str, workspace: Path
    ) -> AgentTranscript:
        """Run the agent inside a Docker container.

        The agent_wrapper.py script runs inside the container, instantiates
        the agent, runs it, and writes the transcript to
        /workspace/.transcript.json. We read it back after the container exits.

        Note: The `agent` parameter is not used directly — the container
        runs its own instance. This parameter exists to satisfy the Sandbox
        protocol and could be used in the future for agent selection.
        """
        self._ensure_image()

        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set in environment. "
                "The Docker sandbox needs it to pass into the container."
            )

        # Convert workspace path for Docker volume mount
        # On Windows, Docker needs forward-slash paths or //c/ style
        workspace_str = str(workspace).replace("\\", "/")

        cmd = [
            "docker", "run", "--rm",
            "--network=none",
            f"--memory={self._memory_limit}",
            f"--cpus={self._cpu_limit}",
            "-v", f"{workspace_str}:/workspace",
            "-e", f"ANTHROPIC_API_KEY={api_key}",
            DOCKER_IMAGE,
            "python", "/app/harness/agent_wrapper.py",
            "--task", task,
            "--workspace", "/workspace",
        ]

        logger.info("DockerSandbox: running container...")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            logger.warning("DockerSandbox: container timed out after %ds", self._timeout_seconds)
            return AgentTranscript(
                tool_calls=[],
                final_response="",
                model="unknown",
                metadata={"error": f"Container timed out after {self._timeout_seconds}s"},
            )

        if result.returncode != 0:
            logger.error(
                "DockerSandbox: container failed (exit %d):\nstdout: %s\nstderr: %s",
                result.returncode,
                result.stdout[-500:] if result.stdout else "",
                result.stderr[-500:] if result.stderr else "",
            )
            return AgentTranscript(
                tool_calls=[],
                final_response="",
                model="unknown",
                metadata={
                    "error": f"Container exited with code {result.returncode}",
                    "stderr": result.stderr[-500:] if result.stderr else "",
                },
            )

        # Read the transcript from the workspace
        transcript_file = workspace / ".transcript.json"
        if not transcript_file.exists():
            logger.error("DockerSandbox: .transcript.json not found in workspace")
            return AgentTranscript(
                tool_calls=[],
                final_response="",
                model="unknown",
                metadata={"error": "Container did not produce .transcript.json"},
            )

        transcript_data = json.loads(
            transcript_file.read_text(encoding="utf-8")
        )
        # Clean up the transcript file so it doesn't appear in workspace diff
        transcript_file.unlink()

        return AgentTranscript.from_dict(transcript_data)

    def cleanup(self, workspace: Path) -> None:
        """Remove the temp directory."""
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
            logger.info("DockerSandbox: cleaned up %s", workspace)
