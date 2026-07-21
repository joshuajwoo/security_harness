"""Data processing pipeline.

Processes CSV data through load, clean, transform, and save stages.
Currently implemented as one monolithic function that needs refactoring.
"""

import csv
import os


def process_data(input_path: str, output_path: str) -> dict:
    """Process a CSV file: load, clean, transform, and save results.

    This function is too long and does too many things. It should be
    refactored into smaller, focused functions.

    Args:
        input_path: Path to the input CSV file.
        output_path: Path to write the processed CSV file.

    Returns:
        A dict with processing statistics.
    """
    # --- LOAD ---
    rows = []
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            rows.append(row)

    if not rows:
        return {"total": 0, "cleaned": 0, "transformed": 0}

    total_count = len(rows)

    # --- CLEAN ---
    cleaned_rows = []
    for row in rows:
        # Skip rows with empty required fields
        if not row.get("name") or not row.get("value"):
            continue
        # Strip whitespace from all fields
        cleaned_row = {}
        for key, val in row.items():
            cleaned_row[key] = val.strip() if isinstance(val, str) else val
        # Skip rows with non-numeric value
        try:
            float(cleaned_row["value"])
        except (ValueError, TypeError):
            continue
        cleaned_rows.append(cleaned_row)

    cleaned_count = len(cleaned_rows)

    # --- TRANSFORM ---
    transformed_rows = []
    for row in cleaned_rows:
        new_row = dict(row)
        value = float(new_row["value"])
        # Normalize value to 0-100 scale
        new_row["value"] = str(round(value * 100, 2))
        # Add uppercase name column
        new_row["name_upper"] = new_row["name"].upper()
        # Add category based on original value
        if value < 0.3:
            new_row["category"] = "low"
        elif value < 0.7:
            new_row["category"] = "medium"
        else:
            new_row["category"] = "high"
        transformed_rows.append(new_row)

    transformed_count = len(transformed_rows)

    # --- SAVE ---
    if transformed_rows:
        output_headers = list(transformed_rows[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=output_headers)
            writer.writeheader()
            writer.writerows(transformed_rows)

    return {
        "total": total_count,
        "cleaned": cleaned_count,
        "transformed": transformed_count,
    }
