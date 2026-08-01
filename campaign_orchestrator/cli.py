"""CLI for Phase D4 automatic campaign orchestration."""

from __future__ import annotations

import argparse
import json

from .engine import OrchestrationEngine
from .executors import CommandExecutor, DemoExecutor
from .models import OrchestratorConfiguration
from .store import OrchestratorStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PrimeAIExplorer automatic campaign orchestrator."
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run_command = subparsers.add_parser("run")
    run_command.add_argument("--campaign-id", required=True)
    run_command.add_argument(
        "--campaign-database",
        required=True,
    )
    run_command.add_argument(
        "--orchestrator-database",
        required=True,
    )
    run_command.add_argument("--worker-id", required=True)
    run_command.add_argument(
        "--executor",
        choices=["demo", "command"],
        default="demo",
    )
    run_command.add_argument("--command-template")
    run_command.add_argument("--working-directory")
    run_command.add_argument("--timeout-seconds", type=float)
    run_command.add_argument(
        "--fail-ordinal",
        action="append",
        type=int,
        default=[],
    )
    run_command.add_argument(
        "--lease-seconds",
        type=int,
        default=900,
    )
    run_command.add_argument(
        "--heartbeat-seconds",
        type=int,
        default=30,
    )
    run_command.add_argument(
        "--max-attempts",
        type=int,
        default=3,
    )
    run_command.add_argument("--max-items", type=int)
    run_command.add_argument(
        "--stop-on-failure",
        action="store_true",
    )
    run_command.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=0.0,
    )
    run_command.add_argument(
        "--poll-seconds",
        type=float,
        default=0.0,
    )

    stop_command = subparsers.add_parser("request-stop")
    stop_command.add_argument("--campaign-id", required=True)
    stop_command.add_argument(
        "--orchestrator-database",
        required=True,
    )
    stop_command.add_argument("--reason")

    clear_command = subparsers.add_parser("clear-stop")
    clear_command.add_argument("--campaign-id", required=True)
    clear_command.add_argument(
        "--orchestrator-database",
        required=True,
    )

    events_command = subparsers.add_parser("events")
    events_command.add_argument("--campaign-id", required=True)
    events_command.add_argument(
        "--orchestrator-database",
        required=True,
    )
    events_command.add_argument("--limit", type=int, default=1000)

    return parser


def main() -> int:
    arguments = build_parser().parse_args()

    if arguments.command == "request-stop":
        store = OrchestratorStore(
            arguments.orchestrator_database
        )
        store.request_stop(
            arguments.campaign_id,
            reason=arguments.reason,
        )
        _print({"stop_requested": True})
        return 0

    if arguments.command == "clear-stop":
        store = OrchestratorStore(
            arguments.orchestrator_database
        )
        store.clear_stop(arguments.campaign_id)
        _print({"stop_requested": False})
        return 0

    if arguments.command == "events":
        store = OrchestratorStore(
            arguments.orchestrator_database
        )
        _print(
            store.list_events(
                arguments.campaign_id,
                limit=arguments.limit,
            )
        )
        return 0

    if arguments.executor == "demo":
        executor = DemoExecutor(
            fail_ordinals=set(arguments.fail_ordinal)
        )
    else:
        if not arguments.command_template:
            raise ValueError(
                "--command-template is required for command executor."
            )
        executor = CommandExecutor(
            arguments.command_template,
            working_directory=arguments.working_directory,
            timeout_seconds=arguments.timeout_seconds,
        )

    configuration = OrchestratorConfiguration(
        campaign_id=arguments.campaign_id,
        worker_id=arguments.worker_id,
        lease_seconds=arguments.lease_seconds,
        heartbeat_seconds=arguments.heartbeat_seconds,
        max_attempts=arguments.max_attempts,
        max_items=arguments.max_items,
        stop_on_failure=arguments.stop_on_failure,
        retry_backoff_seconds=(
            arguments.retry_backoff_seconds
        ),
        poll_seconds=arguments.poll_seconds,
    )

    engine = OrchestrationEngine(
        campaign_database=arguments.campaign_database,
        orchestrator_database=(
            arguments.orchestrator_database
        ),
        executor=executor,
        configuration=configuration,
    )
    _print(engine.run().to_dict())
    return 0


def _print(value) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
