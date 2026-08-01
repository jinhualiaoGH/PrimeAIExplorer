"""Command-line interface for experiment lifecycle management."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .manager import ExperimentManager
from .models import ExperimentRecord, ExperimentSpecification


def load_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}.")

    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PrimeAIExplorer deterministic experiment manager."
    )

    parser.add_argument(
        "--root",
        default="experiments",
        help="Experiment storage root.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    create_parser = subparsers.add_parser(
        "create",
        help="Create or resolve a deterministic experiment.",
    )
    create_parser.add_argument("specification")

    show_parser = subparsers.add_parser(
        "show",
        help="Show experiment state and checkpoint information.",
    )
    show_parser.add_argument("experiment_id")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("experiment_id")

    pause_parser = subparsers.add_parser("pause")
    pause_parser.add_argument("experiment_id")

    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("experiment_id")

    fail_parser = subparsers.add_parser("fail")
    fail_parser.add_argument("experiment_id")
    fail_parser.add_argument("message")

    record_parser = subparsers.add_parser(
        "record",
        help="Append one result record.",
    )
    record_parser.add_argument("experiment_id")
    record_parser.add_argument("record")
    record_parser.add_argument(
        "--failed",
        action="store_true",
        help="Count the case as failed rather than completed.",
    )

    return parser


def specification_from_document(
    document: dict[str, Any],
) -> ExperimentSpecification:
    return ExperimentSpecification(
        name=str(document["name"]),
        sequence_plugin=str(document["sequence_plugin"]),
        sequence_parameters=dict(document["sequence_parameters"]),
        window_sizes=tuple(
            int(value) for value in document["window_sizes"]
        ),
        case_count=int(document["case_count"]),
        prompt_template=str(document["prompt_template"]),
        model_provider=str(document["model_provider"]),
        model_name=str(document["model_name"]),
        model_parameters=dict(document.get("model_parameters", {})),
        random_seed=int(document.get("random_seed", 0)),
        schema_version=str(document.get("schema_version", "1.0")),
    )


def record_from_document(
    document: dict[str, Any],
) -> ExperimentRecord:
    return ExperimentRecord(
        case_id=str(document["case_id"]),
        sequence_index=int(document["sequence_index"]),
        window_size=int(document["window_size"]),
        prompt_sha256=str(document["prompt_sha256"]),
        response_text=str(document["response_text"]),
        parsed_prediction=(
            None
            if document.get("parsed_prediction") is None
            else int(document["parsed_prediction"])
        ),
        actual_value=(
            None
            if document.get("actual_value") is None
            else int(document["actual_value"])
        ),
        is_correct=(
            None
            if document.get("is_correct") is None
            else bool(document["is_correct"])
        ),
        confidence=(
            None
            if document.get("confidence") is None
            else int(document["confidence"])
        ),
        latency_seconds=(
            None
            if document.get("latency_seconds") is None
            else float(document["latency_seconds"])
        ),
        provider_request_id=document.get("provider_request_id"),
        metadata=dict(document.get("metadata", {})),
    )


def main() -> int:
    parser = build_parser()
    arguments = parser.parse_args()

    manager = ExperimentManager(arguments.root)

    if arguments.command == "create":
        document = load_json_object(Path(arguments.specification))
        specification = specification_from_document(document)
        experiment_id, directory = manager.create(specification)

        output = {
            "experiment_id": experiment_id,
            "directory": str(directory),
            "created_or_verified": True,
        }

    elif arguments.command == "show":
        output = manager.summary(arguments.experiment_id)

    elif arguments.command == "start":
        manager.start(arguments.experiment_id)
        output = manager.summary(arguments.experiment_id)

    elif arguments.command == "pause":
        manager.pause(arguments.experiment_id)
        output = manager.summary(arguments.experiment_id)

    elif arguments.command == "complete":
        manager.complete(arguments.experiment_id)
        output = manager.summary(arguments.experiment_id)

    elif arguments.command == "fail":
        manager.fail(arguments.experiment_id, arguments.message)
        output = manager.summary(arguments.experiment_id)

    elif arguments.command == "record":
        document = load_json_object(Path(arguments.record))
        record = record_from_document(document)
        manager.append_record(
            arguments.experiment_id,
            record,
            successful=not arguments.failed,
        )
        output = manager.summary(arguments.experiment_id)

    else:
        parser.error(f"Unsupported command: {arguments.command}")

    print(
        json.dumps(
            output,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
