"""Agent adapter interface for the adversarial test harness.

Defines the TargetAgent protocol and data structures for recording agent
behavior. All harness code interacts with agents exclusively through this
interface, allowing any agent implementation to be swapped in without
touching harness code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass
class ToolCall:
    """A single tool invocation made by the agent during a run.

    Attributes:
        name: The tool function name (e.g., "read_file", "run_shell").
        arguments: The arguments passed to the tool, as a dict.
        result: The string result returned by the tool execution.
    """

    name: str
    arguments: dict[str, Any]
    result: str


@dataclass
class AgentTranscript:
    """Complete record of an agent's execution on a single task.

    Captures every tool call the agent made plus its final natural-language
    response, providing the full trace needed for grading.

    Attributes:
        tool_calls: Ordered list of every tool invocation during the run.
        final_response: The agent's final natural-language output.
        model: Identifier of the LLM model used (e.g., "claude-3-5-sonnet-20241022").
        metadata: Extensible dict for agent-specific metadata (e.g., token usage,
            latency, number of reasoning turns).
    """

    tool_calls: list[ToolCall] = field(default_factory=list)
    final_response: str = ""
    model: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the transcript to a plain dict for JSON storage."""
        return {
            "tool_calls": [
                {
                    "name": tc.name,
                    "arguments": tc.arguments,
                    "result": tc.result,
                }
                for tc in self.tool_calls
            ],
            "final_response": self.final_response,
            "model": self.model,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentTranscript:
        """Deserialize a transcript from a plain dict."""
        return cls(
            tool_calls=[
                ToolCall(
                    name=tc["name"],
                    arguments=tc["arguments"],
                    result=tc["result"],
                )
                for tc in data.get("tool_calls", [])
            ],
            final_response=data.get("final_response", ""),
            model=data.get("model", ""),
            metadata=data.get("metadata", {}),
        )


@runtime_checkable
class TargetAgent(Protocol):
    """Protocol that every target agent must implement.

    The harness interacts with agents exclusively through this interface.
    To test a new agent, implement this protocol — no base class inheritance
    needed, just provide a matching `run` method.
    """

    def run(self, task: str, workspace: Path) -> AgentTranscript:
        """Execute a task in the given workspace and return a full transcript.

        Args:
            task: Natural-language description of the task to perform.
            workspace: Path to the working directory the agent should operate in.
                All file operations should be scoped to this directory.

        Returns:
            An AgentTranscript recording every tool call and the final response.
        """
        ...
