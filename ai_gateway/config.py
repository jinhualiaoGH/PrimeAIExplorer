from __future__ import annotations

import json
from pathlib import Path

from .models import ModelRoute, RetryPolicy
from .registry import GatewayRegistry


def load_gateway_configuration(
    path: str | Path,
) -> tuple[GatewayRegistry, RetryPolicy, dict[str, object]]:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig") as handle:
        document = json.load(handle)

    if not isinstance(document, dict):
        raise ValueError("gateway configuration must be a JSON object.")

    routes = GatewayRegistry(
        ModelRoute(
            alias=str(item["alias"]),
            provider=str(item["provider"]),
            model=str(item["model"]),
            provider_options=dict(item.get("provider_options", {})),
            input_cost_per_million_tokens=(
                float(item["input_cost_per_million_tokens"])
                if item.get("input_cost_per_million_tokens") is not None
                else None
            ),
            output_cost_per_million_tokens=(
                float(item["output_cost_per_million_tokens"])
                if item.get("output_cost_per_million_tokens") is not None
                else None
            ),
        )
        for item in document["routes"]
    )

    retry_document = dict(document.get("retry_policy", {}))
    retry_policy = RetryPolicy(
        max_attempts=int(retry_document.get("max_attempts", 3)),
        initial_backoff_seconds=float(
            retry_document.get("initial_backoff_seconds", 0.25)
        ),
        multiplier=float(retry_document.get("multiplier", 2.0)),
        maximum_backoff_seconds=float(
            retry_document.get("maximum_backoff_seconds", 8.0)
        ),
    )

    options = {
        "requests_per_second": document.get("requests_per_second"),
        "audit_path": document.get("audit_path"),
    }
    return routes, retry_policy, options
