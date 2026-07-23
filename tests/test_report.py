"""Tests for the markdown report generator."""

from __future__ import annotations

from pathlib import Path

from harness.grading.aggregate import GradedResult, HarnessMetrics
from harness.grading.containment import ContainmentCategory, ContainmentResult
from harness.grading.rules import SecurityVerdict
from harness.grading.task_success import CheckType, TaskGrade
from harness.report import generate_markdown_report
from agents.adapter import AgentTranscript, ToolCall

def _mock_graded_result(category: ContainmentCategory) -> GradedResult:
    return GradedResult(
        scenario_id="test_scenario",
        task_id="test_task",
        is_clean=False,
        vector_id="test_vector",
        objective_id="test_objective",
        security_verdict=SecurityVerdict(),
        task_grade=TaskGrade("test_task", True, CheckType.DETERMINISTIC, "ok"),
        containment=ContainmentResult(category, "test evidence", "heuristic"),
        transcript=AgentTranscript(
            tool_calls=[ToolCall("read_file", {"path": "test"}, "content")],
            final_response="done",
            model="test"
        )
    )

def test_generate_markdown_report(tmp_path: Path) -> None:
    metrics = HarnessMetrics(
        total_scenarios=10,
        total_clean=5,
        total_attacked=5,
        clean_task_success_rate=1.0,
        attacked_task_success_rate=0.5,
        non_hijacked_task_success_rate=1.0,
        overall_attack_success_rate=0.5,
        attack_rate_by_vector={"test_vector": 0.5},
        attack_rate_by_objective={"test_objective": 0.5},
        containment_distribution={ContainmentCategory.HIJACKED.value: 1}
    )
    
    results = [
        _mock_graded_result(ContainmentCategory.HIJACKED),
        _mock_graded_result(ContainmentCategory.DISTRACTED_BUT_RECOVERED)
    ]
    
    report_path = tmp_path / "report.md"
    generate_markdown_report(metrics, results, report_path)
    
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    
    # Check headers
    assert "Security Harness Run Report" in content
    assert "High-Level Summary" in content
    assert "Attack Success Breakdowns" in content
    
    # Check metrics
    assert "100.0%" in content  # clean success
    assert "50.0%" in content   # overall attack success
    
    # Check case studies
    assert "Case Study 1: Successful Hijack" in content
    assert "Case Study 2: Distracted but Recovered" in content
    
    # Check transcript excerpt
    assert "read_file" in content
    assert "test_vector" in content
