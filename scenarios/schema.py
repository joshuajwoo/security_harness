"""Pydantic schema for scenario case files.

Every YAML file in scenarios/cases/ must validate against this schema.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator
from scenarios.tasks.task_registry import TASKS
from scenarios.vectors import VECTORS
from scenarios.objectives import OBJECTIVES


class Scenario(BaseModel):
    """Schema for a single test scenario.

    Attributes:
        scenario_id: Unique identifier for this scenario.
        task_id: References a task in the task registry.
        task_prompt: The natural-language task given to the agent.
        fixture_dir: Name of the fixture directory under agents/fixtures/.
        is_clean: True for baseline runs with no injection.
        vector_id: Which injection vector to use (None for clean runs).
        objective_id: Which attack objective (None for clean runs).
        payload: The actual injected text (None for clean runs).
        injection_location: Description of where the payload was planted.
        canary_token: Fake secret planted for exfiltration scenarios.
        success_check: Name of the success check function.
        allowed_modified_files: Files the agent is expected to modify.
    """

    scenario_id: str
    task_id: str
    task_prompt: str
    fixture_dir: str
    is_clean: bool
    vector_id: str | None = None
    objective_id: str | None = None
    payload: str | None = None
    injection_location: str | None = None
    canary_token: str | None = None
    success_check: str
    allowed_modified_files: list[str]

    @field_validator("task_id")
    @classmethod
    def task_must_exist(cls, v: str) -> str:
        if v not in TASKS:
            raise ValueError(f"Unknown task_id: '{v}'. Valid: {list(TASKS.keys())}")
        return v

    @field_validator("vector_id")
    @classmethod
    def vector_must_exist(cls, v: str | None) -> str | None:
        if v is not None and v not in VECTORS:
            raise ValueError(f"Unknown vector_id: '{v}'. Valid: {list(VECTORS.keys())}")
        return v

    @field_validator("objective_id")
    @classmethod
    def objective_must_exist(cls, v: str | None) -> str | None:
        if v is not None and v not in OBJECTIVES:
            raise ValueError(
                f"Unknown objective_id: '{v}'. Valid: {list(OBJECTIVES.keys())}"
            )
        return v

    def model_post_init(self, __context) -> None:
        """Validate cross-field constraints."""
        if self.is_clean:
            if any([self.vector_id, self.objective_id, self.payload]):
                raise ValueError(
                    "Clean scenarios must not have vector_id, objective_id, or payload"
                )
        else:
            if not all([self.vector_id, self.objective_id, self.payload]):
                raise ValueError(
                    "Attacked scenarios must have vector_id, objective_id, and payload"
                )
