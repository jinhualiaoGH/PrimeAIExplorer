"""Deterministic campaign expansion."""

from __future__ import annotations

import hashlib
import itertools

from .canonical import canonical_json_bytes, deterministic_id
from .models import (
    CampaignPlan,
    CampaignSpecification,
    CampaignWorkItem,
)


def expand_campaign(
    specification: CampaignSpecification,
) -> CampaignPlan:
    work_items: list[CampaignWorkItem] = []

    combinations = []
    for provider in sorted(specification.providers):
        for model in sorted(specification.models_by_provider[provider]):
            combinations.extend(
                itertools.product(
                    sorted(specification.dataset_ids),
                    [provider],
                    [model],
                    sorted(specification.prompt_templates),
                    sorted(specification.random_seeds),
                    sorted(specification.window_sizes),
                    range(specification.repeats),
                )
            )

    for ordinal, (
        dataset_id,
        provider,
        model,
        prompt_template,
        random_seed,
        window_size,
        repeat_index,
    ) in enumerate(combinations):
        provider_parameters = dict(
            specification.model_parameters.get(provider, {})
        )
        model_parameters = dict(
            specification.model_parameters.get(
                f"{provider}:{model}",
                {},
            )
        )
        merged_parameters = {
            **provider_parameters,
            **model_parameters,
        }

        identity = {
            "campaign_id": specification.campaign_id,
            "dataset_id": dataset_id,
            "provider": provider,
            "model": model,
            "prompt_template": prompt_template,
            "random_seed": random_seed,
            "window_size": window_size,
            "repeat_index": repeat_index,
            "model_parameters": merged_parameters,
        }

        work_items.append(
            CampaignWorkItem(
                work_item_id=deterministic_id("WI", identity),
                ordinal=ordinal,
                dataset_id=dataset_id,
                provider=provider,
                model=model,
                prompt_template=prompt_template,
                random_seed=random_seed,
                window_size=window_size,
                repeat_index=repeat_index,
                model_parameters=merged_parameters,
            )
        )

    plan_material = {
        "campaign_id": specification.campaign_id,
        "work_items": [item.to_dict() for item in work_items],
    }
    plan_sha256 = hashlib.sha256(
        canonical_json_bytes(plan_material)
    ).hexdigest()

    return CampaignPlan(
        campaign_id=specification.campaign_id,
        plan_sha256=plan_sha256,
        work_items=tuple(work_items),
    )
