from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_backoff_seconds: float = 0.25
    multiplier: float = 2.0
    maximum_backoff_seconds: float = 8.0

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive.")
        if self.initial_backoff_seconds < 0:
            raise ValueError("initial_backoff_seconds must be non-negative.")
        if self.multiplier < 1:
            raise ValueError("multiplier must be at least one.")
        if self.maximum_backoff_seconds < 0:
            raise ValueError("maximum_backoff_seconds must be non-negative.")


@dataclass(frozen=True, slots=True)
class ModelRoute:
    alias: str
    provider: str
    model: str
    provider_options: Mapping[str, Any] = field(default_factory=dict)
    input_cost_per_million_tokens: float | None = None
    output_cost_per_million_tokens: float | None = None

    def __post_init__(self) -> None:
        if not self.alias.strip():
            raise ValueError("alias must not be empty.")
        if not self.provider.strip():
            raise ValueError("provider must not be empty.")
        if not self.model.strip():
            raise ValueError("model must not be empty.")


@dataclass(frozen=True, slots=True)
class GatewayRequest:
    route: str
    prompt: str
    system_prompt: str | None = None
    temperature: float | None = 0.0
    max_output_tokens: int | None = None
    seed: int | None = None
    json_mode: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.route.strip():
            raise ValueError("route must not be empty.")
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty.")


@dataclass(frozen=True, slots=True)
class GatewayUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GatewayResponse:
    route: str
    provider: str
    model: str
    text: str
    latency_seconds: float
    attempts: int
    request_id: str | None
    finish_reason: str | None
    usage: GatewayUsage
    provider_metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "provider": self.provider,
            "model": self.model,
            "text": self.text,
            "latency_seconds": self.latency_seconds,
            "attempts": self.attempts,
            "request_id": self.request_id,
            "finish_reason": self.finish_reason,
            "usage": self.usage.to_dict(),
            "provider_metadata": dict(self.provider_metadata),
        }
