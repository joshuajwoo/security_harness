# Security Harness

An adversarial test harness that measures both **attack containment** (security) and **task completion** (utility) for tool-using coding agents.

Modeled on the [AgentDojo](https://github.com/ethz-spylab/agentdojo) utility-and-security framing: an agent that "passes" by refusing everything isn't useful, and one that completes every task but follows injected instructions isn't safe. This harness measures both axes simultaneously.

---

## What it does

This harness evaluates coding agents against **indirect prompt injection** attacks. It sets up realistic coding tasks (e.g., "fix this bug," "refactor this file") but secretly plants malicious instructions within the workspace context (e.g., inside a code comment, a README, or mock API output).

It then grades the agent's run on two axes:
1. **Security (Attack Success):** Did the agent succumb to the injected attack? Measured via deterministic rules (did it leak a planted canary token, modify out-of-scope files, or run dangerous shell commands like `curl` or `rm -rf`).
2. **Utility (Task Success):** Did the agent still complete its legitimate job? Measured via deterministic checks like test suite passes and expected file outputs.

Additionally, the harness classifies the agent's **containment behavior** into four categories to understand *how* it handled the attack: `hijacked`, `noticed_and_refused`, `distracted_but_recovered`, or `clean_ignore`.

## Quick start

### Setup
1. Create a virtual environment and install dependencies using `uv`:
   ```bash
   uv sync --extra dev
   ```
2. Set up your environment variables:
   ```bash
   cp .env.example .env
   # Add your ANTHROPIC_API_KEY (used by the baseline ToyAgent)
   ```
3. Build the Docker sandbox image (required for secure execution):
   ```bash
   docker build -t security-harness-sandbox .
   ```

### Running the Harness

Run all scenarios (36 cases) and generate a markdown report:
```bash
# Run in the Docker sandbox (recommended)
uv run python -m harness.run_all --sandbox docker --report

# Or run a single specific scenario for debugging
uv run python -m harness.run_all --scenario clean_fix_bug_01
```

The run transcripts (JSON) and the final Markdown report will be saved to the `reports/` directory.

## Project structure

| Directory     | Purpose                                    |
|---------------|--------------------------------------------|
| `agents/`     | Target agents (`ToyAgent`) and the `TargetAgent` adapter interface |
| `scenarios/`  | Attack scenario YAML definitions and raw source fixtures |
| `harness/`    | The execution runner, Docker/process sandboxing, and grading logic |
| `tests/`      | Comprehensive unit tests for the harness infrastructure itself |
| `reports/`    | Generated run transcripts and aggregate markdown reports |

## Architecture & Grading Pipeline

The runner operates as follows:
1. **Setup:** The scenario fixture is copied to a temporary sandbox directory, and if the scenario is an "attack", the malicious payload (and canary token) is injected into the code context.
2. **Execution:** The target agent is invoked and given the task prompt. Its tool calls and final response are recorded into a transcript.
3. **Grading:**
   - **Rule-based security checks (`harness/grading/rules.py`):** Deterministic checks for canary leaks, unauthorized file changes, or dangerous commands.
   - **Task success grading (`harness/grading/task_success.py`):** Deterministic checks verifying if the agent actually accomplished its task.
   - **Containment classifier (`harness/grading/containment.py`):** Determines the agent's posture (hijacked vs. distracted/refused/ignored).
   - **Aggregation (`harness/grading/aggregate.py`):** Computes overall attack success and task success rates.

## What's Next

- **Phase 5 (Real Agents):** Build adapters (implementing `agents.adapter.TargetAgent`) to point the harness at your own production agents, establishing a baseline comparison against the `ToyAgent`.
- **Phase 6 (LLM Judges):** Integrate LLM-as-a-judge for subjective tasks (e.g., grading qualitative output) or to improve the containment classifier.
