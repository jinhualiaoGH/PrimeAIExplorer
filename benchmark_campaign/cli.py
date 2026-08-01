"""CLI for deterministic benchmark campaigns."""

from __future__ import annotations

import argparse
import json

from .expansion import expand_campaign
from .io import (
    load_plan,
    load_specification,
    write_json_object,
)
from .manager import CampaignManager
from .specification import build_specification


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PrimeAIExplorer benchmark campaign manager."
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    build_command = subparsers.add_parser("build-spec")
    build_command.add_argument("--name", required=True)
    build_command.add_argument("--description", default="")
    build_command.add_argument(
        "--dataset-id",
        action="append",
        required=True,
    )
    build_command.add_argument(
        "--provider-model",
        action="append",
        required=True,
        help="provider=model",
    )
    build_command.add_argument(
        "--prompt-template",
        action="append",
        required=True,
    )
    build_command.add_argument(
        "--random-seed",
        action="append",
        type=int,
        required=True,
    )
    build_command.add_argument(
        "--window-size",
        action="append",
        type=int,
        required=True,
    )
    build_command.add_argument("--repeats", type=int, default=1)
    build_command.add_argument("--output", required=True)

    expand_command = subparsers.add_parser("expand")
    expand_command.add_argument("specification")
    expand_command.add_argument("--output", required=True)

    create_command = subparsers.add_parser("create")
    create_command.add_argument("plan")
    create_command.add_argument("--database", required=True)

    status_command = subparsers.add_parser("status")
    status_command.add_argument("campaign_id")
    status_command.add_argument("--database", required=True)

    claim_command = subparsers.add_parser("claim-next")
    claim_command.add_argument("campaign_id")
    claim_command.add_argument("--database", required=True)

    complete_command = subparsers.add_parser("complete")
    complete_command.add_argument("campaign_id")
    complete_command.add_argument("work_item_id")
    complete_command.add_argument("--database", required=True)
    complete_command.add_argument(
        "--experiment-id",
        required=True,
    )
    complete_command.add_argument("--catalog-record-id")

    fail_command = subparsers.add_parser("fail")
    fail_command.add_argument("campaign_id")
    fail_command.add_argument("work_item_id")
    fail_command.add_argument("--database", required=True)
    fail_command.add_argument(
        "--error-message",
        required=True,
    )

    reset_command = subparsers.add_parser("reset-failed")
    reset_command.add_argument("campaign_id")
    reset_command.add_argument("--database", required=True)

    list_command = subparsers.add_parser("list-items")
    list_command.add_argument("campaign_id")
    list_command.add_argument("--database", required=True)
    list_command.add_argument("--status")
    list_command.add_argument("--limit", type=int, default=1000)
    list_command.add_argument("--offset", type=int, default=0)

    export_command = subparsers.add_parser("export-plan")
    export_command.add_argument("campaign_id")
    export_command.add_argument("--database", required=True)
    export_command.add_argument("--output", required=True)

    return parser


def main() -> int:
    arguments = build_parser().parse_args()

    if arguments.command == "build-spec":
        models_by_provider: dict[str, list[str]] = {}
        for value in arguments.provider_model:
            if "=" not in value:
                raise ValueError(
                    "--provider-model must use provider=model."
                )
            provider, model = value.split("=", 1)
            models_by_provider.setdefault(provider, []).append(
                model
            )

        specification = build_specification(
            name=arguments.name,
            description=arguments.description,
            dataset_ids=arguments.dataset_id,
            providers=tuple(models_by_provider),
            models_by_provider=models_by_provider,
            prompt_templates=arguments.prompt_template,
            random_seeds=arguments.random_seed,
            window_sizes=arguments.window_size,
            repeats=arguments.repeats,
        )
        write_json_object(
            arguments.output,
            specification.to_dict(),
        )
        _print(specification.to_dict())
        return 0

    if arguments.command == "expand":
        plan = expand_campaign(
            load_specification(arguments.specification)
        )
        write_json_object(arguments.output, plan.to_dict())
        _print(plan.to_dict())
        return 0

    manager = CampaignManager(arguments.database)

    if arguments.command == "create":
        plan = load_plan(arguments.plan)
        inserted = manager.create(plan)
        _print(
            {
                "campaign_id": plan.campaign_id,
                "inserted": inserted,
                "work_item_count": len(plan.work_items),
            }
        )
        return 0

    if arguments.command == "status":
        _print(manager.status(arguments.campaign_id).to_dict())
        return 0

    if arguments.command == "claim-next":
        item = manager.claim_next(arguments.campaign_id)
        _print(item.to_dict() if item is not None else None)
        return 0

    if arguments.command == "complete":
        item = manager.complete(
            arguments.campaign_id,
            arguments.work_item_id,
            experiment_id=arguments.experiment_id,
            catalog_record_id=arguments.catalog_record_id,
        )
        _print(item.to_dict())
        return 0

    if arguments.command == "fail":
        item = manager.fail(
            arguments.campaign_id,
            arguments.work_item_id,
            error_message=arguments.error_message,
        )
        _print(item.to_dict())
        return 0

    if arguments.command == "reset-failed":
        count = manager.reset_failed(arguments.campaign_id)
        _print({"reset_count": count})
        return 0

    if arguments.command == "list-items":
        items = manager.list_items(
            arguments.campaign_id,
            status=arguments.status,
            limit=arguments.limit,
            offset=arguments.offset,
        )
        _print([item.to_dict() for item in items])
        return 0

    destination = manager.export_plan_jsonl(
        arguments.campaign_id,
        arguments.output,
    )
    _print({"output": str(destination.resolve())})
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
