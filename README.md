# Security Harness
An adversarial test harness that measures both **attack containment** (security) and **task completion** (utility) for tool-using coding agents.

Modeled on the [AgentDojo](https://github.com/ethz-spylab/agentdojo) utility-and-security framing: an agent that "passes" by refusing everything isn't useful, and one that completes every task but follows injected instructions isn't safe. This harness measures both axes simultaneously.

## What it does

- Runs a target agent against realistic coding tasks with **indirect prompt injections** embedded in the workspace (code comments, READMEs, fake tool output, filenames).
- Grades each run on two axes: did the attack succeed, and did the agent still complete its real task.
- Produces a report with attack success rates broken down by injection vector and objective type, plus task success rates on clean vs. attacked runs.

## Quick start

```bash
cp .env.example .env          # Add your ANTHROPIC_API_KEY
uv sync --extra dev           # Install dependencies
uv run pytest                 # Run tests
```

## Project structure

| Directory     | Purpose                                    |
|---------------|--------------------------------------------|
| `agents/`     | Target agents and the adapter interface    |
| `scenarios/`  | Attack scenario definitions and fixtures   |
| `harness/`    | Runner, sandboxing, and grading logic      |
| `reports/`    | Generated output (gitignored)              |
| `tests/`      | Unit tests for the harness itself          |
