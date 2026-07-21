"""Validate all scenario YAML files against the Pydantic schema.

Run with: uv run python scenarios/validate_scenarios.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from scenarios.schema import Scenario

CASES_DIR = Path(__file__).parent / "cases"


def validate_all() -> bool:
    """Validate every YAML file in cases/ against the Scenario schema.

    Returns:
        True if all files are valid, False otherwise.
    """
    yaml_files = sorted(CASES_DIR.glob("*.yaml"))

    if not yaml_files:
        print(f"ERROR: No .yaml files found in {CASES_DIR}")
        return False

    errors = []
    valid_count = 0

    for filepath in yaml_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                errors.append((filepath.name, "File is empty"))
                continue

            Scenario(**data)
            valid_count += 1

        except yaml.YAMLError as e:
            errors.append((filepath.name, f"YAML parse error: {e}"))
        except ValidationError as e:
            errors.append((filepath.name, f"Schema validation error:\n{e}"))
        except Exception as e:
            errors.append((filepath.name, f"Unexpected error: {e}"))

    # Print results
    total = len(yaml_files)
    print(f"\nValidation Results: {valid_count}/{total} scenarios valid")
    print(f"{'=' * 50}")

    if errors:
        print(f"\n{len(errors)} ERRORS:")
        for filename, error in errors:
            print(f"\n  ❌ {filename}")
            for line in str(error).split("\n"):
                print(f"     {line}")
        return False

    # Print summary statistics
    clean = sum(1 for f in yaml_files
                if yaml.safe_load(f.read_text()).get("is_clean", False))
    attacked = total - clean

    print(f"\n  ✅ All {total} scenarios are valid")
    print(f"     Clean:    {clean}")
    print(f"     Attacked: {attacked}")
    return True


if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)
