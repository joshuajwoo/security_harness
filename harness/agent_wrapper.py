"""Agent wrapper — runs inside the Docker container.

This is the entry point for containerized agent execution. It:
1. Parses CLI arguments (task prompt and workspace path)
2. Instantiates the ToyAgent (using ANTHROPIC_API_KEY from env)
3. Runs the agent on the task
4. Writes the transcript as JSON to /workspace/.transcript.json

The host-side DockerSandbox reads the transcript after the container exits.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an agent inside the Docker sandbox"
    )
    parser.add_argument(
        "--task",
        required=True,
        help="The natural-language task prompt for the agent",
    )
    parser.add_argument(
        "--workspace",
        required=True,
        help="Path to the workspace directory (mounted volume)",
    )
    parser.add_argument(
        "--agent",
        default="toy",
        choices=["toy"],
        help="Which agent to use (default: toy)",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace)
    if not workspace.is_dir():
        print(f"ERROR: workspace '{workspace}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Import here so this file can be parsed without all dependencies
    from agents.toy_agent import ToyAgent

    agent = ToyAgent()
    transcript = agent.run(args.task, workspace)

    # Write transcript to the workspace for the host to read
    transcript_path = workspace / ".transcript.json"
    transcript_data = transcript.to_dict()
    transcript_path.write_text(
        json.dumps(transcript_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Transcript written to {transcript_path}")
    print(f"Tool calls: {len(transcript.tool_calls)}")
    print(f"Model: {transcript.model}")


if __name__ == "__main__":
    main()
