from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.exceptions import ConfigurationError


@dataclass
class ServiceRegistry:
    _services: dict[str, Any] = field(default_factory=dict)

    def register(
        self,
        service_id: str,
        service: Any,
        *,
        replace: bool = False,
    ) -> None:
        normalized = self._normalize_id(service_id)
        if normalized in self._services and not replace:
            raise ConfigurationError(
                f"Service is already registered: {normalized}"
            )
        self._services[normalized] = service

    def resolve(self, service_id: str) -> Any:
        normalized = self._normalize_id(service_id)
        if normalized not in self._services:
            raise ConfigurationError(
                f"Service is not registered: {normalized}"
            )
        return self._services[normalized]

    def contains(self, service_id: str) -> bool:
        return self._normalize_id(service_id) in self._services

    def unregister(self, service_id: str) -> Any:
        normalized = self._normalize_id(service_id)
        if normalized not in self._services:
            raise ConfigurationError(
                f"Service is not registered: {normalized}"
            )
        return self._services.pop(normalized)

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._services))

    @staticmethod
    def _normalize_id(service_id: str) -> str:
        if not isinstance(service_id, str):
            raise ConfigurationError("service_id must be text.")
        normalized = service_id.strip()
        if not normalized:
            raise ConfigurationError("service_id must not be empty.")
        return normalized
