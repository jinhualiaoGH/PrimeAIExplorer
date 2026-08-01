from __future__ import annotations

from dataclasses import dataclass, field

from kernel.exceptions import ConfigurationError
from sequence_api.protocols import SequenceProvider


@dataclass
class SequenceProviderRegistry:
    _providers: dict[str, SequenceProvider] = field(
        default_factory=dict
    )

    def register(
        self,
        provider: SequenceProvider,
        *,
        replace: bool = False,
    ) -> None:
        if not isinstance(provider, SequenceProvider):
            raise ConfigurationError(
                "Provider does not implement SequenceProvider."
            )
        sequence_id = provider.sequence_id.strip()
        if not sequence_id:
            raise ConfigurationError(
                "Provider sequence_id must not be empty."
            )
        if sequence_id in self._providers and not replace:
            raise ConfigurationError(
                f"Provider is already registered: {sequence_id}"
            )
        self._providers[sequence_id] = provider

    def resolve(self, sequence_id: str) -> SequenceProvider:
        if not isinstance(sequence_id, str):
            raise ConfigurationError(
                "sequence_id must be text."
            )
        normalized = sequence_id.strip()
        if normalized not in self._providers:
            raise ConfigurationError(
                f"Sequence provider is not registered: {normalized}"
            )
        return self._providers[normalized]

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
