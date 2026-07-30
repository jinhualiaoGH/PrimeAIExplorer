"""Connector registration and model-independent execution service."""

from __future__ import annotations

from dataclasses import dataclass, field

from connectors.base import BaseConnector
from connectors.models import ConnectorRequest, ConnectorResponse


@dataclass(slots=True)
class ConnectorService:
    """In-memory connector registry and execution service."""

    _connectors: dict[str, BaseConnector] = field(default_factory=dict)

    def register(
        self,
        connector: BaseConnector,
        *,
        replace: bool = False,
    ) -> None:
        connector_id = connector.connector_id

        if connector_id in self._connectors and not replace:
            raise ValueError(
                f"Connector already registered: {connector_id}"
            )

        self._connectors[connector_id] = connector

    def get(self, connector_id: str) -> BaseConnector:
        try:
            return self._connectors[connector_id]
        except KeyError as error:
            raise KeyError(
                f"Connector is not registered: {connector_id}"
            ) from error

    def execute(
        self,
        request: ConnectorRequest,
    ) -> ConnectorResponse:
        connector = self.get(request.connector_id)
        return connector.execute(request)

    def registered_connector_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._connectors))


__all__ = ["ConnectorService"]
