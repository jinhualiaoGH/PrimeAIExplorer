from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


class ProviderError(RuntimeError):
    """Normalized provider failure."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable


@dataclass(frozen=True)
class ProviderRequest:
    model: str
    prompt: str
    system_prompt: str | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None
    seed: int | None = None
    json_mode: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    text: str
    request_id: str | None = None
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    provider_metadata: Mapping[str, Any] = field(default_factory=dict)


class ProviderAdapter(ABC):
    provider_name: str

    @abstractmethod
    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError

    @abstractmethod
    def health(self, *, live: bool = False) -> dict[str, Any]:
        raise NotImplementedError
