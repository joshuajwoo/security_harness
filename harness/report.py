"""Markdown report generator for harness runs.

Takes the aggregated metrics and the list of graded results, and produces
a formatted markdown report detailing overall scores, breakdowns by vector
and objective, and 2-3 case studies of interesting agent behavior.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from harness.grading.aggregate import GradedResult, HarnessMetrics
from harness.grading.containment import ContainmentCategory


def _write_header(f: TextIO, metrics: HarnessMetrics, timestamp: str) -> None:
    f.write(f"# Security Harness Run Report\n\n")
    f.write(f"**Date:** {timestamp}\n\n")
    f.write(
        f"**Scenarios:** {metrics.total_scenarios} total "
        f"({metrics.total_clean} clean, {metrics.total_attacked} attacked)\n\n"
    )

    f.write("## High-Level Summary\n\n")
    f.write("| Axis | Metric | Score |\n")
    f.write("|---|---|---|\n")
    f.write(f"| **Utility** | Task Success (Clean runs) | {metrics.clean_task_success_rate:.1%} |\n")
    f.write(f"| **Utility** | Task Success (Attacked runs) | {metrics.attacked_task_success_rate:.1%} |\n")
    f.write(f"| **Utility** | Task Success (Attacked, non-hijacked) | {metrics.non_hijacked_task_success_rate:.1%} |\n")
    f.write(f"| **Security**| Overall Attack Success Rate | {metrics.overall_attack_success_rate:.1%} |\n")
    f.write("\n")


def _write_breakdowns(f: TextIO, metrics: HarnessMetrics) -> None:
    f.write("## Attack Success Breakdowns\n\n")
    
    if metrics.attack_rate_by_vector:
        f.write("### By Injection Vector\n\n")
        f.write("| Vector | Attack Success Rate |\n")
        f.write("|---|---|\n")
        for vector, rate in sorted(metrics.attack_rate_by_vector.items(), key=lambda x: x[1], reverse=True):
            f.write(f"| `{vector}` | {rate:.1%} |\n")
        f.write("\n")

    if metrics.attack_rate_by_objective:
        f.write("### By Attack Objective\n\n")
        f.write("| Objective | Attack Success Rate |\n")
        f.write("|---|---|\n")
        for obj, rate in sorted(metrics.attack_rate_by_objective.items(), key=lambda x: x[1], reverse=True):
            f.write(f"| `{obj}` | {rate:.1%} |\n")
        f.write("\n")

    if metrics.containment_distribution:
        f.write("### Containment Distribution (Attacked Runs)\n\n")
        f.write("| Category | Count | % |\n")
        f.write("|---|---|---|\n")
        total = sum(metrics.containment_distribution.values())
        for cat in ContainmentCategory:
            count = metrics.containment_distribution.get(cat.value, 0)
            pct = (count / total) if total > 0 else 0
            f.write(f"| `{cat.value}` | {count} | {pct:.1%} |\n")
        f.write("\n")


def _write_case_study(f: TextIO, result: GradedResult, title: str) -> None:
    f.write(f"### {title}\n\n")
    f.write(f"- **Scenario:** `{result.scenario_id}`\n")
    f.write(f"- **Task:** `{result.task_id}`\n")
    f.write(f"- **Vector:** `{result.vector_id}`\n")
    f.write(f"- **Objective:** `{result.objective_id}`\n")
    
    if result.containment:
        f.write(f"- **Containment:** `{result.containment.category.value}` ({result.containment.evidence})\n")
    
    f.write(f"- **Task Success:** {'✅ PASS' if result.task_grade.success else '❌ FAIL'}\n\n")

    # Dump the tool calls as a condensed transcript
    f.write("**Transcript Excerpt:**\n")
    f.write("```json\n")
    
    # We load it back from dict to strip some fields if needed, or just dump as formatted JSON
    transcript_dict = {
        "final_response": result.transcript.final_response,
        "tool_calls": [
            {
                "name": tc.name,
                "arguments": tc.arguments,
                # Truncate result if it's too long
                "result": str(tc.result)[:200] + ("..." if tc.result and len(str(tc.result)) > 200 else "")
            }
            for tc in result.transcript.tool_calls
        ]
    }
    
    f.write(json.dumps(transcript_dict, indent=2))
    f.write("\n```\n\n")


def _write_case_studies(f: TextIO, results: list[GradedResult]) -> None:
    f.write("## Case Studies\n\n")
    
    # Try to find a hijacked run
    hijacked = next((r for r in results if r.containment and r.containment.category == ContainmentCategory.HIJACKED), None)
    if hijacked:
        _write_case_study(f, hijacked, "Case Study 1: Successful Hijack")
    else:
        f.write("No hijacked runs found for a case study.\n\n")

    # Try to find a distracted but recovered run
    distracted = next((r for r in results if r.containment and r.containment.category == ContainmentCategory.DISTRACTED_BUT_RECOVERED), None)
    if distracted:
        _write_case_study(f, distracted, "Case Study 2: Distracted but Recovered")
    else:
        # Fallback to noticed and refused
        refused = next((r for r in results if r.containment and r.containment.category == ContainmentCategory.NOTICED_AND_REFUSED), None)
        if refused:
            _write_case_study(f, refused, "Case Study 2: Noticed and Refused")


def generate_markdown_report(
    metrics: HarnessMetrics,
    results: list[GradedResult],
    output_path: Path
) -> Path:
    """Generate a markdown report and save it to output_path."""
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w", encoding="utf-8") as f:
        _write_header(f, metrics, timestamp)
        _write_breakdowns(f, metrics)
        _write_case_studies(f, results)
        
    return output_path
