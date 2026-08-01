from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kernel.context import ExecutionContext
from kernel.exceptions import ValidationError
from sequence_api.models import (
    SequenceBatch,
    SequenceBatchRequest,
    SequenceWindowRequest,
)
from sequence_api.providers import InMemorySequenceProvider
from sequence_api.registry import SequenceProviderRegistry


@dataclass
class SequenceExecutionPlugin:
    configuration: Mapping[str, Any] | None = None

    plugin_id = "sequence_api"

    def __post_init__(self) -> None:
        configuration = dict(self.configuration or {})
        self.registry = SequenceProviderRegistry()

        providers = configuration.get("providers", ())
        for provider_configuration in providers:
            self.registry.register(
                InMemorySequenceProvider.from_configuration(
                    provider_configuration
                )
            )

    def health_check(self, context: ExecutionContext) -> bool:
        return bool(context.session_id.strip())

    def execute(
        self,
        payload: Any,
        context: ExecutionContext,
    ) -> Any:
        if not isinstance(payload, Mapping):
            raise ValidationError(
                "Sequence API payload must be a mapping."
            )
        operation = payload.get("operation")
        if operation == "describe":
            return self._describe(payload, context)
        if operation == "window":
            return self._window(payload, context)
        if operation == "batch":
            return self._batch(payload, context)
        if operation == "list":
            return {
                "schema_version": "1.0",
                "sequence_ids": list(
                    self.registry.registered_ids()
                ),
            }
        raise ValidationError(
            f"Unsupported sequence operation: {operation!r}"
        )

    def _describe(
        self,
        payload: Mapping[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        provider = self.registry.resolve(payload["sequence_id"])
        return provider.describe(context).to_dict()

    def _window(
        self,
        payload: Mapping[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        request = SequenceWindowRequest.from_mapping(payload)
        provider = self.registry.resolve(request.sequence_id)
        return provider.read_window(request, context).to_dict()

    def _batch(
        self,
        payload: Mapping[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        raw_requests = payload.get("requests")
        if not isinstance(raw_requests, list):
            raise ValidationError(
                "Batch payload must contain a requests list."
            )
        request = SequenceBatchRequest(
            tuple(
                SequenceWindowRequest.from_mapping(entry)
                for entry in raw_requests
            )
        )
        windows = tuple(
            self.registry.resolve(entry.sequence_id).read_window(
                entry,
                context,
            )
            for entry in request.requests
        )
        return SequenceBatch(windows).to_dict()
