"""Serialization for campaign specifications and plans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import (
    CampaignPlan,
    CampaignSpecification,
    CampaignWorkItem,
)


def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{source} must contain a JSON object.")
    return value


def write_json_object(path: str | Path, document: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return destination


def load_specification(path: str | Path) -> CampaignSpecification:
    document = load_json_object(path)
    return specification_from_document(document)


def load_plan(path: str | Path) -> CampaignPlan:
    document = load_json_object(path)
    return plan_from_document(document)


def specification_from_document(
    document: Mapping[str, Any],
) -> CampaignSpecification:
    return CampaignSpecification(
        campaign_id=str(document["campaign_id"]),
        name=str(document["name"]),
        description=str(document.get("description", "")),
        schema_version=str(document.get("schema_version", "1.0")),
        dataset_ids=tuple(str(item) for item in document["dataset_ids"]),
        providers=tuple(str(item) for item in document["providers"]),
        models_by_provider={
            str(provider): tuple(str(model) for model in models)
            for provider, models in document["models_by_provider"].items()
        },
        prompt_templates=tuple(
            str(item) for item in document["prompt_templates"]
        ),
        random_seeds=tuple(
            int(item) for item in document["random_seeds"]
        ),
        window_sizes=tuple(
            int(item) for item in document["window_sizes"]
        ),
        repeats=int(document.get("repeats", 1)),
        model_parameters={
            str(key): dict(value)
            for key, value in document.get(
                "model_parameters",
                {},
            ).items()
        },
        metadata=dict(document.get("metadata", {})),
    )


def plan_from_document(document: Mapping[str, Any]) -> CampaignPlan:
    work_items = tuple(
        CampaignWorkItem(
            work_item_id=str(item["work_item_id"]),
            ordinal=int(item["ordinal"]),
            dataset_id=str(item["dataset_id"]),
            provider=str(item["provider"]),
            model=str(item["model"]),
            prompt_template=str(item["prompt_template"]),
            random_seed=int(item["random_seed"]),
            window_size=int(item["window_size"]),
            repeat_index=int(item["repeat_index"]),
            model_parameters=dict(item.get("model_parameters", {})),
            status=str(item.get("status", "pending")),
            experiment_id=(
                str(item["experiment_id"])
                if item.get("experiment_id") is not None
                else None
            ),
            catalog_record_id=(
                str(item["catalog_record_id"])
                if item.get("catalog_record_id") is not None
                else None
            ),
            attempts=int(item.get("attempts", 0)),
            error_message=(
                str(item["error_message"])
                if item.get("error_message") is not None
                else None
            ),
        )
        for item in document["work_items"]
    )

    return CampaignPlan(
        campaign_id=str(document["campaign_id"]),
        plan_sha256=str(document["plan_sha256"]),
        work_items=work_items,
    )
