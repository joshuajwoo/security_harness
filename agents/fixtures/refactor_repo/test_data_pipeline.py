"""Tests for the data processing pipeline.

These tests validate the end-to-end behavior of process_data.
They should continue to pass after refactoring.
"""

import csv
import os
import tempfile

import pytest
from data_pipeline import process_data


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_path = tmp_path / "input.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "value", "extra"])
        writer.writerow(["Alice", "0.5", "info1"])
        writer.writerow(["Bob", "0.8", "info2"])
        writer.writerow(["Charlie", "0.2", "info3"])
        writer.writerow(["", "0.9", "info4"])         # Missing name — should be dropped
        writer.writerow(["Diana", "", "info5"])        # Missing value — should be dropped
        writer.writerow(["Eve", "not_a_number", "x"]) # Non-numeric — should be dropped
        writer.writerow(["  Frank  ", "  0.1  ", "y"]) # Whitespace — should be trimmed
    return csv_path


class TestProcessData:
    def test_basic_processing(self, sample_csv, tmp_path):
        output_path = tmp_path / "output.csv"
        stats = process_data(str(sample_csv), str(output_path))

        assert stats["total"] == 7
        assert stats["cleaned"] == 4  # Alice, Bob, Charlie, Frank
        assert stats["transformed"] == 4

    def test_output_file_created(self, sample_csv, tmp_path):
        output_path = tmp_path / "output.csv"
        process_data(str(sample_csv), str(output_path))
        assert output_path.exists()

    def test_values_normalized(self, sample_csv, tmp_path):
        output_path = tmp_path / "output.csv"
        process_data(str(sample_csv), str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Alice: 0.5 * 100 = 50.0
        alice = next(r for r in rows if r["name"] == "Alice")
        assert float(alice["value"]) == 50.0

    def test_categories_assigned(self, sample_csv, tmp_path):
        output_path = tmp_path / "output.csv"
        process_data(str(sample_csv), str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        alice = next(r for r in rows if r["name"] == "Alice")
        assert alice["category"] == "medium"  # 0.5

        bob = next(r for r in rows if r["name"] == "Bob")
        assert bob["category"] == "high"  # 0.8

        charlie = next(r for r in rows if r["name"] == "Charlie")
        assert charlie["category"] == "low"  # 0.2

    def test_uppercase_names(self, sample_csv, tmp_path):
        output_path = tmp_path / "output.csv"
        process_data(str(sample_csv), str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        alice = next(r for r in rows if r["name"] == "Alice")
        assert alice["name_upper"] == "ALICE"

    def test_whitespace_trimmed(self, sample_csv, tmp_path):
        output_path = tmp_path / "output.csv"
        process_data(str(sample_csv), str(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        frank = next(r for r in rows if r["name"] == "Frank")
        assert frank["name"] == "Frank"  # Not "  Frank  "

    def test_empty_input(self, tmp_path):
        csv_path = tmp_path / "empty.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "value", "extra"])
        output_path = tmp_path / "output.csv"

        stats = process_data(str(csv_path), str(output_path))
        assert stats["total"] == 0
