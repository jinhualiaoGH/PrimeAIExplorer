from __future__ import annotations

import json

import pytest

from ai_gateway import (
    AIGateway,
    GatewayRegistry,
    GatewayRequest,
    ModelRoute,
    RetryPolicy,
)
from ai_gateway.audit import JsonlAuditSink
from model_providers import ProviderRegistry
from model_providers.core import (
    ProviderCapabilities,
    ProviderResponse,
    ProviderUsage,
)


class FixtureProvider:
    name = "fixture"
    capabilities = ProviderCapabilities(True, True, True)

    def __init__(self, *, failures=0, counter=None):
        self.failures = failures
        self.counter = counter if counter is not None else {"calls": 0}

    def generate(self, request):
        self.counter["calls"] += 1
        if self.counter["calls"] <= self.failures:
            raise RuntimeError("HTTP 429: controlled rate limit")
        return ProviderResponse(
            provider=self.name,
            model=request.model,
            text="6",
            latency_seconds=0.125,
            request_id="req-1",
            finish_reason="stop",
            usage=ProviderUsage(100, 20, 120),
            metadata={"case_id": request.metadata.get("case_id")},
        )


def make_gateway(*, failures=0, audit_path=None, sleep=lambda _: None):
    counter = {"calls": 0}
    providers = ProviderRegistry()
    providers.register(
        "fixture",
        lambda **_: FixtureProvider(
            failures=failures,
            counter=counter,
        ),
    )
    routes = GatewayRegistry(
        [
            ModelRoute(
                alias="primary",
                provider="fixture",
                model="fixture-model",
                input_cost_per_million_tokens=1.0,
                output_cost_per_million_tokens=2.0,
            )
        ]
    )
    gateway = AIGateway(
        routes=routes,
        providers=providers,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_backoff_seconds=0.0,
        ),
        audit_sink=(
            JsonlAuditSink(audit_path)
            if audit_path is not None
            else None
        ),
        sleep=sleep,
    )
    return gateway, counter


def test_alias_routes_to_existing_provider():
    gateway, counter = make_gateway()

    response = gateway.invoke(
        GatewayRequest(
            route="primary",
            prompt="Predict.",
            metadata={"case_id": "CASE-1"},
        )
    )

    assert response.provider == "fixture"
    assert response.model == "fixture-model"
    assert response.text == "6"
    assert response.attempts == 1
    assert counter["calls"] == 1


def test_transient_failure_retries():
    gateway, counter = make_gateway(failures=2)

    response = gateway.invoke(
        GatewayRequest(route="primary", prompt="Predict.")
    )

    assert response.attempts == 3
    assert counter["calls"] == 3


def test_nontransient_failure_is_not_retried():
    providers = ProviderRegistry()
    providers.register(
        "fixture",
        lambda **_: type(
            "P",
            (),
            {
                "name": "fixture",
                "capabilities": ProviderCapabilities(),
                "generate": lambda self, request: (_ for _ in ()).throw(
                    ValueError("invalid request")
                ),
            },
        )(),
    )
    gateway = AIGateway(
        routes=GatewayRegistry(
            [ModelRoute("x", "fixture", "m")]
        ),
        providers=providers,
        retry_policy=RetryPolicy(max_attempts=3),
        sleep=lambda _: None,
    )

    with pytest.raises(ValueError, match="invalid request"):
        gateway.invoke(GatewayRequest(route="x", prompt="x"))


def test_cost_estimate_is_normalized():
    gateway, _ = make_gateway()
    response = gateway.invoke(
        GatewayRequest(route="primary", prompt="Predict.")
    )

    assert response.usage.estimated_cost_usd == pytest.approx(
        100 / 1_000_000 + 2 * 20 / 1_000_000
    )


def test_audit_jsonl_is_secret_safe(tmp_path):
    path = tmp_path / "audit.jsonl"
    gateway, _ = make_gateway(audit_path=path)
    gateway.invoke(
        GatewayRequest(
            route="primary",
            prompt="Predict.",
            metadata={"api_key": "do-not-store"},
        )
    )

    text = path.read_text(encoding="utf-8")
    assert "do-not-store" not in text
    document = json.loads(text)
    assert document["event"] == "gateway_request_completed"


def test_health_and_route_ordering():
    gateway, _ = make_gateway()
    health = gateway.health()

    assert health == [
        {
            "alias": "primary",
            "provider": "fixture",
            "model": "fixture-model",
            "configured": True,
            "live_checked": False,
            "healthy": True,
            "error": None,
        }
    ]
