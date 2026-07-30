"""Abstract model-independent connector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from connectors.models import ConnectorRequest, ConnectorResponse


@dataclass(frozen=True, slots=True)
class ConnectorCapabilities:
    supports_system_messages: bool
    supports_developer_messages: bool
    supports_structured_output: bool
    supports_seed: bool
    supports_temperature: bool
    supports_tools: bool
    supports_streaming: bool
    supports_usage_reporting: bool
    supports_exact_model_revision: bool
    maximum_context_tokens: int | None = None
    maximum_output_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "supports_system_messages": self.supports_system_messages,
            "supports_developer_messages": (
                self.supports_developer_messages
            ),
            "supports_structured_output": (
                self.supports_structured_output
            ),
            "supports_seed": self.supports_seed,
            "supports_temperature": self.supports_temperature,
            "supports_tools": self.supports_tools,
            "supports_streaming": self.supports_streaming,
            "supports_usage_reporting": (
                self.supports_usage_reporting
            ),
            "supports_exact_model_revision": (
                self.supports_exact_model_revision
            ),
            "maximum_context_tokens": self.maximum_context_tokens,
            "maximum_output_tokens": self.maximum_output_tokens,
        }


class BaseConnector(ABC):
    """Canonical connector interface."""

    connector_id: str
    connector_version: str
    title: str
    connector_type: str
    external_access: bool
    cost_class: str

    @property
    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        """Return declared connector capabilities."""

    @abstractmethod
    def execute(
        self,
        request: ConnectorRequest,
    ) -> ConnectorResponse:
        """Execute one canonical connector request."""

    def validate_request(
        self,
        request: ConnectorRequest,
    ) -> None:
        """Validate connector ownership and basic capabilities."""

        if request.connector_id != self.connector_id:
            raise ValueError(
                "Request connector ID does not match connector instance."
            )

        if request.connector_version != self.connector_version:
            raise ValueError(
                "Request connector version does not match connector instance."
            )

        has_system = any(
            message.role.value == "system"
            for message in request.messages
        )

        if has_system and not self.capabilities.supports_system_messages:
            raise ValueError(
                "Connector does not support system messages."
            )


__all__ = [
    "BaseConnector",
    "ConnectorCapabilities",
]
