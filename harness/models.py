"""Data models for harness execution results.

These models capture everything about a single scenario run — the scenario
definition, the agent's transcript, workspace changes, and grading signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from agents.adapter import AgentTranscript
from scenarios.schema import Scenario


@dataclass
class WorkspaceDiff:
    """Files that were added, modified, or deleted during a run.

    Attributes:
        added: Files that didn't exist before the run.
        modified: Files that existed before but were changed.
        deleted: Files that existed before but were removed.
    """

    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "added": self.added,
            "modified": self.modified,
            "deleted": self.deleted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkspaceDiff:
        return cls(
            added=data.get("added", []),
            modified=data.get("modified", []),
            deleted=data.get("deleted", []),
        )


@dataclass
class RunResult:
    """Complete result of running one scenario.

    Attributes:
        scenario: The scenario that was executed.
        transcript: The agent's full tool-call transcript.
        workspace_diff: Files added/modified/deleted during the run.
        canary_leaked: True if the canary token appeared outside its original
            location. None for non-exfiltration scenarios.
        task_success: Whether the agent completed the legitimate task
            (per the scenario's success check).
        duration_seconds: Wall-clock time for the run.
        error: Error message if the run crashed, None otherwise.
        timestamp: When the run started.
        agent_name: Identifier for the agent that was tested.
    """

    scenario: Scenario
    transcript: AgentTranscript
    workspace_diff: WorkspaceDiff = field(default_factory=WorkspaceDiff)
    canary_leaked: bool | None = None
    task_success: bool = False
    duration_seconds: float = 0.0
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_name: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict suitable for JSON storage."""
        return {
            "scenario_id": self.scenario.scenario_id,
            "task_id": self.scenario.task_id,
            "is_clean": self.scenario.is_clean,
            "vector_id": self.scenario.vector_id,
            "objective_id": self.scenario.objective_id,
            "transcript": self.transcript.to_dict(),
            "workspace_diff": self.workspace_diff.to_dict(),
            "canary_leaked": self.canary_leaked,
            "task_success": self.task_success,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "timestamp": self.timestamp,
            "agent_name": self.agent_name,
        }
