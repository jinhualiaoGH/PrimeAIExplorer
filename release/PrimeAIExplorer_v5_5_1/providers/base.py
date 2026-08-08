from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    text: str
    latency_ms: int
    usage: dict[str, Any]


class ProviderConnector(Protocol):
    name: str

    def validate(self) -> None:
        ...

    def execute(
        self,
        case: dict[str, Any],
        *,
        timeout_seconds: int,
    ) -> ProviderResult:
        ...
