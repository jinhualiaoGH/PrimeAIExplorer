"""CLI for Phase C2 checkpointed batch execution."""

from __future__ import annotations

import argparse
import json
from typing import Any

from experiment_manager import ExperimentManager

from .loading import load_batch_plan, load_executor
from .runner import BatchRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PrimeAIExplorer checkpointed batch runner."
    )
    parser.add_argument(
        "--root",
        default="experiments",
        help="Experiment storage root.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Execute or resume a deterministic batch plan.",
    )
    run_parser.add_argument("plan")
    run_parser.add_argument(
        "--executor",
        required=True,
        help="Executor reference: package.module:function_name",
    )
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--max-cases", type=int)
    run_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-case JSON progress events.",
    )

    return parser


def main() -> int:
    arguments = build_parser().parse_args()

    manager = ExperimentManager(arguments.root)
    runner = BatchRunner(manager)
    plan = load_batch_plan(arguments.plan)
    executor = load_executor(arguments.executor)

    def progress(event: dict[str, object]) -> None:
        if not arguments.quiet:
            print(json.dumps(event, sort_keys=True), flush=True)

    summary = runner.run(
        plan,
        executor,
        dry_run=arguments.dry_run,
        max_cases=arguments.max_cases,
        progress=progress,
    )

    print(json.dumps(summary.to_dict(), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
