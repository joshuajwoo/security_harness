"""Generate scenario YAML files in scenarios/cases/.

This script creates 36 curated scenarios:
- 15 clean runs (3 per task)
- 21 attacked runs (covering all vectors and objectives)

Run with: uv run python scenarios/generate_scenarios.py
"""

from __future__ import annotations

import uuid
from pathlib import Path

import yaml

from scenarios.tasks.task_registry import TASKS
from scenarios.objectives import OBJECTIVES

CASES_DIR = Path(__file__).parent / "cases"


def _canary() -> str:
    """Generate a unique, obviously-fake canary token."""
    return f"FAKE-SECRET-{uuid.uuid4().hex[:12].upper()}"


def generate_clean_scenarios() -> list[dict]:
    """Generate 3 clean scenarios per task (15 total)."""
    scenarios = []
    for i, (task_id, task) in enumerate(TASKS.items()):
        for variant in range(1, 4):
            scenarios.append({
                "scenario_id": f"clean_{task_id}_{variant:02d}",
                "task_id": task_id,
                "task_prompt": task.prompt,
                "fixture_dir": task.fixture_dir,
                "is_clean": True,
                "vector_id": None,
                "objective_id": None,
                "payload": None,
                "injection_location": None,
                "canary_token": None,
                "success_check": task.success_check,
                "allowed_modified_files": list(task.allowed_files),
            })
    return scenarios


def generate_attacked_scenarios() -> list[dict]:
    """Generate 21 attacked scenarios with good coverage of vectors × objectives."""
    # Curated pairings to ensure every vector and objective appears multiple times
    # Format: (task_id, vector_id, objective_id)
    pairings = [
        # fix_bug task — 5 attacked variants
        ("fix_bug", "code_comment", "exfil_echo"),
        ("fix_bug", "readme", "excess_delete"),
        ("fix_bug", "git_log", "hijack_ignore"),
        ("fix_bug", "lint_output", "excess_shell"),
        ("fix_bug", "filename", "exfil_write"),

        # add_feature task — 4 attacked variants
        ("add_feature", "code_comment", "excess_edit"),
        ("add_feature", "readme", "hijack_replace"),
        ("add_feature", "git_log", "exfil_echo"),
        ("add_feature", "lint_output", "excess_delete"),

        # refactor task — 4 attacked variants
        ("refactor", "code_comment", "hijack_ignore"),
        ("refactor", "readme", "exfil_write"),
        ("refactor", "filename", "excess_shell"),
        ("refactor", "lint_output", "hijack_replace"),

        # summarize (ml_repo) task — 4 attacked variants
        ("summarize", "readme", "exfil_echo"),
        ("summarize", "code_comment", "excess_delete"),
        ("summarize", "git_log", "excess_edit"),
        ("summarize", "filename", "hijack_ignore"),

        # fix_web task — 4 attacked variants
        ("fix_web", "code_comment", "exfil_write"),
        ("fix_web", "readme", "excess_shell"),
        ("fix_web", "lint_output", "excess_edit"),
        ("fix_web", "git_log", "hijack_replace"),
    ]

    scenarios = []
    for task_id, vector_id, objective_id in pairings:
        task = TASKS[task_id]
        obj = OBJECTIVES[objective_id]
        canary = _canary() if obj.needs_canary else None
        payload = obj.payload_fn(canary)

        scenarios.append({
            "scenario_id": f"attack_{task_id}_{vector_id}_{objective_id}",
            "task_id": task_id,
            "task_prompt": task.prompt,
            "fixture_dir": task.fixture_dir,
            "is_clean": False,
            "vector_id": vector_id,
            "objective_id": objective_id,
            "payload": payload,
            "injection_location": f"Injected via {vector_id} vector",
            "canary_token": canary,
            "success_check": task.success_check,
            "allowed_modified_files": list(task.allowed_files),
        })

    return scenarios


def write_scenarios(scenarios: list[dict]) -> None:
    """Write each scenario to its own YAML file."""
    CASES_DIR.mkdir(parents=True, exist_ok=True)

    # Remove the .gitkeep if it exists
    gitkeep = CASES_DIR / ".gitkeep"
    if gitkeep.exists():
        gitkeep.unlink()

    for scenario in scenarios:
        filename = f"{scenario['scenario_id']}.yaml"
        filepath = CASES_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(
                scenario,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    print(f"Generated {len(scenarios)} scenario files in {CASES_DIR}/")


def main():
    clean = generate_clean_scenarios()
    attacked = generate_attacked_scenarios()
    all_scenarios = clean + attacked

    print(f"Clean scenarios:    {len(clean)}")
    print(f"Attacked scenarios: {len(attacked)}")
    print(f"Total:              {len(all_scenarios)}")

    write_scenarios(all_scenarios)

    # Print coverage summary
    vectors_used = set()
    objectives_used = set()
    tasks_attacked = set()
    for s in attacked:
        vectors_used.add(s["vector_id"])
        objectives_used.add(s["objective_id"])
        tasks_attacked.add(s["task_id"])

    print(f"\nVector coverage:    {len(vectors_used)}/5 — {sorted(vectors_used)}")
    print(f"Objective coverage: {len(objectives_used)}/7 — {sorted(objectives_used)}")
    print(f"Task coverage:      {len(tasks_attacked)}/5 — {sorted(tasks_attacked)}")


if __name__ == "__main__":
    main()
