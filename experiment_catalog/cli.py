"""CLI for Phase D2 experiment registry and search."""

from __future__ import annotations

import argparse
import json

from .catalog import ExperimentCatalog
from .models import SearchQuery
from .snapshots import build_catalog_record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PrimeAIExplorer persistent experiment catalog."
    )
    parser.add_argument(
        "--database",
        required=True,
        help="SQLite catalog database path.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_command = subparsers.add_parser("register")
    register_command.add_argument("experiment_directory")
    register_command.add_argument("--dataset-manifest")
    register_command.add_argument("--analysis-json")
    register_command.add_argument("--report-manifest")

    search_command = subparsers.add_parser("search")
    search_command.add_argument("--experiment-id")
    search_command.add_argument("--dataset-id")
    search_command.add_argument("--provider")
    search_command.add_argument("--model")
    search_command.add_argument("--status")
    search_command.add_argument("--sequence-type")
    search_command.add_argument("--min-accuracy", type=float)
    search_command.add_argument("--max-accuracy", type=float)
    search_command.add_argument("--text")
    search_command.add_argument("--limit", type=int, default=100)
    search_command.add_argument("--offset", type=int, default=0)

    show_command = subparsers.add_parser("show")
    show_command.add_argument("record_id")

    history_command = subparsers.add_parser("history")
    history_command.add_argument("experiment_id")

    latest_command = subparsers.add_parser("latest")
    latest_command.add_argument("experiment_id")

    export_command = subparsers.add_parser("export")
    export_command.add_argument("output")

    subparsers.add_parser("count")

    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    catalog = ExperimentCatalog(arguments.database)

    if arguments.command == "register":
        record = build_catalog_record(
            arguments.experiment_directory,
            dataset_manifest=arguments.dataset_manifest,
            analysis_json=arguments.analysis_json,
            report_manifest=arguments.report_manifest,
        )
        inserted = catalog.register(record)
        print(
            json.dumps(
                {
                    "inserted": inserted,
                    "record": record.to_dict(),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if arguments.command == "search":
        records = catalog.search(
            SearchQuery(
                experiment_id=arguments.experiment_id,
                dataset_id=arguments.dataset_id,
                provider=arguments.provider,
                model=arguments.model,
                status=arguments.status,
                sequence_type=arguments.sequence_type,
                min_accuracy=arguments.min_accuracy,
                max_accuracy=arguments.max_accuracy,
                text=arguments.text,
                limit=arguments.limit,
                offset=arguments.offset,
            )
        )
        _print_records(records)
        return 0

    if arguments.command == "show":
        print(
            json.dumps(
                catalog.get(arguments.record_id).to_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if arguments.command == "history":
        _print_records(catalog.history(arguments.experiment_id))
        return 0

    if arguments.command == "latest":
        record = catalog.latest_for_experiment(arguments.experiment_id)
        print(
            json.dumps(
                record.to_dict() if record is not None else None,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if arguments.command == "export":
        destination = catalog.export_jsonl(arguments.output)
        print(
            json.dumps(
                {
                    "count": catalog.count(),
                    "output": str(destination.resolve()),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(json.dumps({"count": catalog.count()}, indent=2))
    return 0


def _print_records(records) -> None:
    print(
        json.dumps(
            [record.to_dict() for record in records],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
