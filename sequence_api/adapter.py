from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kernel.context import ExecutionContext
from kernel.exceptions import ValidationError
from sequence_api.memmap_provider import (
    NpyMemmapSequenceProvider,
)
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

        for provider_configuration in configuration.get(
            "providers",
            (),
        ):
            provider_type = provider_configuration.get(
                "provider_type",
                "in_memory",
            )
            if provider_type == "in_memory":
                provider = (
                    InMemorySequenceProvider.from_configuration(
                        provider_configuration
                    )
                )
            elif provider_type == "numpy_npy_memmap":
                provider = (
                    NpyMemmapSequenceProvider.from_configuration(
                        provider_configuration
                    )
                )
            else:
                raise ValidationError(
                    f"Unsupported provider_type: {provider_type!r}"
                )
            self.registry.register(provider)

    def health_check(self, context: ExecutionContext) -> bool:
        return bool(context.session_id.strip())

    def close(self) -> None:
        for sequence_id in self.registry.registered_ids():
            provider = self.registry.resolve(sequence_id)
            closer = getattr(provider, "close", None)
            if closer is not None:
                closer()

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
