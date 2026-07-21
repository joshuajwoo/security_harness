"""End-to-end test for the ToyAgent against the sample_repo fixture.

This test requires a valid ANTHROPIC_API_KEY in the .env file and makes
real API calls. It is marked with @pytest.mark.manual so it won't run
in the default test suite — run it explicitly with:

    uv run pytest tests/test_toy_agent.py -m manual -v

The test verifies the full loop:
1. The sample_repo has a failing test (off-by-one bug in factorial).
2. The ToyAgent is given the task to fix it.
3. After the agent runs, the test suite passes.
4. The returned AgentTranscript contains at least one tool call.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from agents.adapter import AgentTranscript, TargetAgent
from agents.toy_agent import ToyAgent

# Path to the sample_repo fixture
SAMPLE_REPO = Path(__file__).parent.parent / "agents" / "fixtures" / "sample_repo"


@pytest.mark.manual
class TestToyAgentEndToEnd:
    """End-to-end tests requiring a live Anthropic API key."""

    def test_sample_repo_has_failing_test(self):
        """Precondition: the fixture itself has a failing test."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_math_utils.py", "-v"],
            cwd=str(SAMPLE_REPO),
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "Expected sample_repo tests to FAIL before the agent runs, "
            "but they passed. The fixture's bug may have been accidentally fixed."
        )

    def test_agent_fixes_failing_test(self, tmp_path: Path):
        """The agent should find and fix the bug, making all tests pass."""
        # Copy fixture to a temp directory so the original is untouched
        workspace = tmp_path / "sample_repo"
        shutil.copytree(SAMPLE_REPO, workspace)

        # Run the agent
        agent: TargetAgent = ToyAgent()
        transcript: AgentTranscript = agent.run(
            task="There's a failing test in this repo. Find the bug and fix it.",
            workspace=workspace,
        )

        # Verify the transcript recorded tool calls
        assert len(transcript.tool_calls) > 0, (
            "Agent should have made at least one tool call."
        )
        assert transcript.final_response, (
            "Agent should have produced a final response."
        )
        assert transcript.model, "Agent should record which model was used."

        # Verify the test suite now passes
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_math_utils.py", "-v"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Expected tests to pass after agent fix, but they failed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}\n"
            f"Agent tool calls: {[tc.name for tc in transcript.tool_calls]}\n"
            f"Agent final response: {transcript.final_response[:500]}"
        )

    def test_agent_transcript_is_serializable(self, tmp_path: Path):
        """The transcript should round-trip through dict serialization."""
        workspace = tmp_path / "sample_repo"
        shutil.copytree(SAMPLE_REPO, workspace)

        agent: TargetAgent = ToyAgent()
        transcript = agent.run(
            task="List the files in this repo and tell me what it contains.",
            workspace=workspace,
        )

        # Round-trip through dict
        data = transcript.to_dict()
        restored = AgentTranscript.from_dict(data)

        assert len(restored.tool_calls) == len(transcript.tool_calls)
        assert restored.final_response == transcript.final_response
        assert restored.model == transcript.model


class TestToyAgentUnit:
    """Unit tests that don't require an API key."""

    def test_implements_target_agent_protocol(self):
        """ToyAgent should satisfy the TargetAgent protocol."""
        assert isinstance(ToyAgent, type)
        # Check the protocol structurally
        agent = ToyAgent.__new__(ToyAgent)
        assert isinstance(agent, TargetAgent)

    def test_adapter_dataclasses(self):
        """ToolCall and AgentTranscript should work as expected."""
        from agents.adapter import ToolCall, AgentTranscript

        tc = ToolCall(name="read_file", arguments={"path": "foo.py"}, result="content")
        assert tc.name == "read_file"

        transcript = AgentTranscript(
            tool_calls=[tc],
            final_response="Done.",
            model="test-model",
        )
        data = transcript.to_dict()
        assert data["tool_calls"][0]["name"] == "read_file"
        assert data["final_response"] == "Done."

        restored = AgentTranscript.from_dict(data)
        assert restored.tool_calls[0].name == "read_file"
        assert restored.final_response == "Done."
