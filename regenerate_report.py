import json
from pathlib import Path

from harness.run_all import load_scenarios, CASES_DIR, REPORTS_DIR, REPORT_OUTPUT_FILE
from harness.grading.rules import run_security_checks
from harness.grading.task_success import grade_task_success
from harness.grading.containment import classify_containment
from harness.grading.aggregate import GradedResult, aggregate_metrics, print_metrics
from harness.report import generate_markdown_report
from harness.models import RunResult, WorkspaceDiff
from agents.adapter import AgentTranscript


def main():
    # Load scenarios so we have the full definitions (for grading rules)
    scenarios_by_id = {s.scenario_id: s for s in load_scenarios(CASES_DIR)}
    
    if not REPORTS_DIR.exists():
        print(f"Error: No reports directory found at {REPORTS_DIR}")
        return

    json_files = list(REPORTS_DIR.glob("*.json"))
    if not json_files:
        print(f"Error: No JSON run results found in {REPORTS_DIR}")
        return

    print(f"Found {len(json_files)} saved run results. Grading locally...")
    
    graded_results = []
    
    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        scenario_id = data.get("scenario_id")
        if scenario_id not in scenarios_by_id:
            print(f"Warning: Scenario {scenario_id} from {filepath.name} not found in current YAMLs. Skipping.")
            continue
            
        scenario = scenarios_by_id[scenario_id]
        
        # Reconstruct RunResult from the saved JSON
        result = RunResult(
            scenario=scenario,
            transcript=AgentTranscript.from_dict(data.get("transcript", {})),
            workspace_diff=WorkspaceDiff.from_dict(data.get("workspace_diff", {})),
            canary_leaked=data.get("canary_leaked"),
            task_success=data.get("task_success", False),
            duration_seconds=data.get("duration_seconds", 0.0),
            error=data.get("error"),
            timestamp=data.get("timestamp", ""),
            agent_name=data.get("agent_name", "unknown")
        )
        
        # Run grading checks
        sec_verdict = run_security_checks(result)
        task_grade = grade_task_success(result)
        
        containment = None
        if not scenario.is_clean:
            containment = classify_containment(result.transcript, sec_verdict)
            
        graded = GradedResult(
            scenario_id=scenario.scenario_id,
            task_id=scenario.task_id,
            is_clean=scenario.is_clean,
            vector_id=scenario.vector_id,
            objective_id=scenario.objective_id,
            security_verdict=sec_verdict,
            task_grade=task_grade,
            containment=containment,
            transcript=result.transcript,
        )
        graded_results.append(graded)

    # Aggregate and generate report
    metrics = aggregate_metrics(graded_results)
    print_metrics(metrics)
    
    report_path = generate_markdown_report(metrics, graded_results, REPORT_OUTPUT_FILE)
    print(f"\nSuccessfully regenerated report at: {report_path}")


if __name__ == "__main__":
    main()
