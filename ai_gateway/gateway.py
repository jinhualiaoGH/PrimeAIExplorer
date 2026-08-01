from __future__ import annotations

import time
from typing import Any, Callable

from model_providers import ModelRequest, ProviderRegistry, default_registry

from .audit import JsonlAuditSink
from .classification import is_transient_error
from .models import (
    GatewayRequest,
    GatewayResponse,
    GatewayUsage,
    RetryPolicy,
)
from .rate_limit import FixedIntervalLimiter
from .registry import GatewayRegistry


class AIGateway:
    def __init__(
        self,
        *,
        routes: GatewayRegistry,
        providers: ProviderRegistry | None = None,
        retry_policy: RetryPolicy | None = None,
        requests_per_second: float | None = None,
        audit_sink: JsonlAuditSink | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.routes = routes
        self.providers = providers or default_registry()
        self.retry_policy = retry_policy or RetryPolicy()
        self.limiter = FixedIntervalLimiter(
            requests_per_second,
            sleep=sleep,
        )
        self.audit_sink = audit_sink
        self.sleep = sleep

    def invoke(self, request: GatewayRequest) -> GatewayResponse:
        route = self.routes.resolve(request.route)
        provider = self.providers.create(
            route.provider,
            **dict(route.provider_options),
        )

        provider_request = ModelRequest(
            prompt=request.prompt,
            model=route.model,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
            seed=request.seed,
            json_mode=request.json_mode,
            metadata=dict(request.metadata),
        )

        last_error: BaseException | None = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self.limiter.acquire()
            try:
                response = provider.generate(provider_request)
            except Exception as error:
                last_error = error
                retry = (
                    attempt < self.retry_policy.max_attempts
                    and is_transient_error(error)
                )
                self._audit(
                    {
                        "event": "gateway_attempt_failed",
                        "route": route.alias,
                        "provider": route.provider,
                        "model": route.model,
                        "attempt": attempt,
                        "retry": retry,
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                    }
                )
                if not retry:
                    raise
                self.sleep(self._backoff(attempt))
                continue

            usage = GatewayUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.total_tokens,
                estimated_cost_usd=self._estimate_cost(
                    route.input_cost_per_million_tokens,
                    route.output_cost_per_million_tokens,
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                ),
            )
            gateway_response = GatewayResponse(
                route=route.alias,
                provider=response.provider,
                model=response.model,
                text=response.text,
                latency_seconds=response.latency_seconds,
                attempts=attempt,
                request_id=response.request_id,
                finish_reason=response.finish_reason,
                usage=usage,
                provider_metadata=dict(response.metadata),
            )
            self._audit(
                {
                    "event": "gateway_request_completed",
                    **gateway_response.to_dict(),
                }
            )
            return gateway_response

        assert last_error is not None
        raise last_error

    def health(self, *, live: bool = False) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for route in self.routes.list_routes():
            entry: dict[str, Any] = {
                "alias": route.alias,
                "provider": route.provider,
                "model": route.model,
                "configured": True,
                "live_checked": live,
                "healthy": True,
                "error": None,
            }
            try:
                self.providers.create(
                    route.provider,
                    **dict(route.provider_options),
                )
                if live:
                    response = self.invoke(
                        GatewayRequest(
                            route=route.alias,
                            prompt="Return the word OK.",
                            temperature=0.0,
                            max_output_tokens=8,
                        )
                    )
                    entry["healthy"] = bool(response.text.strip())
            except Exception as error:
                entry["healthy"] = False
                entry["error"] = f"{type(error).__name__}: {error}"
            results.append(entry)
        return results

    def _backoff(self, attempt: int) -> float:
        value = (
            self.retry_policy.initial_backoff_seconds
            * (self.retry_policy.multiplier ** (attempt - 1))
        )
        return min(value, self.retry_policy.maximum_backoff_seconds)

    @staticmethod
    def _estimate_cost(
        input_rate: float | None,
        output_rate: float | None,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> float | None:
        if input_rate is None and output_rate is None:
            return None
        if input_tokens is None and output_tokens is None:
            return None

        input_cost = (
            0.0
            if input_rate is None or input_tokens is None
            else input_rate * input_tokens / 1_000_000
        )
        output_cost = (
            0.0
            if output_rate is None or output_tokens is None
            else output_rate * output_tokens / 1_000_000
        )
        return input_cost + output_cost

    def _audit(self, event: dict[str, Any]) -> None:
        if self.audit_sink is not None:
            self.audit_sink.write(event)
