"""Immutable models for benchmark campaigns."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


_ALLOWED_ITEM_STATUSES = {
    "pending",
    "running",
    "completed",
    "failed",
    "skipped",
}


@dataclass(frozen=True, slots=True)
class CampaignSpecification:
    campaign_id: str
    name: str
    description: str
    schema_version: str
    dataset_ids: tuple[str, ...]
    providers: tuple[str, ...]
    models_by_provider: Mapping[str, tuple[str, ...]]
    prompt_templates: tuple[str, ...]
    random_seeds: tuple[int, ...]
    window_sizes: tuple[int, ...]
    repeats: int = 1
    model_parameters: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.campaign_id.startswith("CMP-"):
            raise ValueError("campaign_id must begin with 'CMP-'.")
        if not self.name.strip():
            raise ValueError("name must not be empty.")
        if not self.dataset_ids:
            raise ValueError("dataset_ids must not be empty.")
        if not self.providers:
            raise ValueError("providers must not be empty.")
        if not self.prompt_templates:
            raise ValueError("prompt_templates must not be empty.")
        if not self.random_seeds:
            raise ValueError("random_seeds must not be empty.")
        if not self.window_sizes:
            raise ValueError("window_sizes must not be empty.")
        if self.repeats <= 0:
            raise ValueError("repeats must be positive.")

        for provider in self.providers:
            models = self.models_by_provider.get(provider, ())
            if not models:
                raise ValueError(
                    f"provider '{provider}' must have at least one model."
                )

        if any(size <= 0 for size in self.window_sizes):
            raise ValueError("window sizes must be positive.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "description": self.description,
            "schema_version": self.schema_version,
            "dataset_ids": list(self.dataset_ids),
            "providers": list(self.providers),
            "models_by_provider": {
                key: list(value)
                for key, value in sorted(self.models_by_provider.items())
            },
            "prompt_templates": list(self.prompt_templates),
            "random_seeds": list(self.random_seeds),
            "window_sizes": list(self.window_sizes),
            "repeats": self.repeats,
            "model_parameters": {
                key: dict(value)
                for key, value in sorted(self.model_parameters.items())
            },
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CampaignWorkItem:
    work_item_id: str
    ordinal: int
    dataset_id: str
    provider: str
    model: str
    prompt_template: str
    random_seed: int
    window_size: int
    repeat_index: int
    model_parameters: Mapping[str, Any]
    status: str = "pending"
    experiment_id: str | None = None
    catalog_record_id: str | None = None
    attempts: int = 0
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not self.work_item_id.startswith("WI-"):
            raise ValueError("work_item_id must begin with 'WI-'.")
        if self.ordinal < 0:
            raise ValueError("ordinal must be non-negative.")
        if self.status not in _ALLOWED_ITEM_STATUSES:
            raise ValueError(f"invalid work item status: {self.status}")
        if self.repeat_index < 0:
            raise ValueError("repeat_index must be non-negative.")
        if self.attempts < 0:
            raise ValueError("attempts must be non-negative.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["model_parameters"] = dict(self.model_parameters)
        return result


@dataclass(frozen=True, slots=True)
class CampaignPlan:
    campaign_id: str
    plan_sha256: str
    work_items: tuple[CampaignWorkItem, ...]

    def __post_init__(self) -> None:
        if len(self.plan_sha256) != 64:
            raise ValueError("plan_sha256 must have 64 hexadecimal characters.")
        int(self.plan_sha256, 16)

        ordinals = [item.ordinal for item in self.work_items]
        if ordinals != list(range(len(self.work_items))):
            raise ValueError("work item ordinals must be contiguous.")

        identifiers = [item.work_item_id for item in self.work_items]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("work_item_id values must be unique.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "plan_sha256": self.plan_sha256,
            "work_items": [item.to_dict() for item in self.work_items],
        }


@dataclass(frozen=True, slots=True)
class CampaignStatus:
    campaign_id: str
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    skipped: int
    progress_fraction: float
    next_pending_ordinal: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
