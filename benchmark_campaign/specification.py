"""Build deterministic campaign specifications."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .canonical import deterministic_id
from .models import CampaignSpecification


def build_specification(
    *,
    name: str,
    description: str,
    dataset_ids: Sequence[str],
    providers: Sequence[str],
    models_by_provider: Mapping[str, Sequence[str]],
    prompt_templates: Sequence[str],
    random_seeds: Sequence[int],
    window_sizes: Sequence[int],
    repeats: int = 1,
    model_parameters: Mapping[str, Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
    schema_version: str = "1.0",
) -> CampaignSpecification:
    provisional = {
        "name": name,
        "description": description,
        "schema_version": schema_version,
        "dataset_ids": sorted(str(item) for item in dataset_ids),
        "providers": sorted(str(item) for item in providers),
        "models_by_provider": {
            str(provider): sorted(str(model) for model in models)
            for provider, models in sorted(models_by_provider.items())
        },
        "prompt_templates": sorted(
            str(item) for item in prompt_templates
        ),
        "random_seeds": sorted(int(item) for item in random_seeds),
        "window_sizes": sorted(int(item) for item in window_sizes),
        "repeats": int(repeats),
        "model_parameters": {
            str(key): dict(value)
            for key, value in sorted(
                (model_parameters or {}).items()
            )
        },
        "metadata": dict(metadata or {}),
    }
    campaign_id = deterministic_id("CMP", provisional)

    return CampaignSpecification(
        campaign_id=campaign_id,
        name=name,
        description=description,
        schema_version=schema_version,
        dataset_ids=tuple(provisional["dataset_ids"]),
        providers=tuple(provisional["providers"]),
        models_by_provider={
            key: tuple(value)
            for key, value in provisional[
                "models_by_provider"
            ].items()
        },
        prompt_templates=tuple(
            provisional["prompt_templates"]
        ),
        random_seeds=tuple(provisional["random_seeds"]),
        window_sizes=tuple(provisional["window_sizes"]),
        repeats=repeats,
        model_parameters={
            key: dict(value)
            for key, value in provisional[
                "model_parameters"
            ].items()
        },
        metadata=dict(provisional["metadata"]),
    )
