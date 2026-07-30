"""Registration and deterministic execution of PrimeAIExplorer observatories."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

from .base import Observatory
from .result import ObservatoryResult


class ObservatoryManager:
    """Register, inspect, and execute observatories in registration order."""

    def __init__(self, observatories: Sequence[Observatory] | None = None) -> None:
        self._observatories: OrderedDict[str, Observatory] = OrderedDict()
        for observatory in observatories or ():
            self.register(observatory)

    @staticmethod
    def _validated_observatory_name(observatory: Observatory) -> str:
        if not isinstance(observatory, Observatory):
            raise TypeError("observatory must implement Observatory.")
        name = getattr(observatory, "name", None)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("observatory name must be a non-empty string.")
        return name.strip()

    def register(self, observatory: Observatory) -> None:
        """Register one observatory, rejecting duplicate names."""

        name = self._validated_observatory_name(observatory)
        if name in self._observatories:
            raise ValueError(f"observatory {name!r} is already registered.")
        self._observatories[name] = observatory

    def names(self) -> tuple[str, ...]:
        """Return names in deterministic registration order."""

        return tuple(self._observatories)

    def get(self, name: str) -> Observatory:
        """Return a registered observatory by exact name."""

        try:
            return self._observatories[name]
        except KeyError as exc:
            raise KeyError(f"unknown observatory: {name!r}") from exc

    def run(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any] | None = None,
    ) -> Mapping[str, ObservatoryResult]:
        """Run every registered observatory in deterministic order."""

        if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
            raise TypeError("records must be a sequence of mappings.")
        normalized_records: tuple[Mapping[str, Any], ...] = tuple(
            self._validated_record(record, index)
            for index, record in enumerate(records, start=1)
        )
        if context is None:
            normalized_context: Mapping[str, Any] = MappingProxyType({})
        elif not isinstance(context, Mapping):
            raise TypeError("context must be a mapping.")
        else:
            normalized_context = MappingProxyType(dict(context))

        results: OrderedDict[str, ObservatoryResult] = OrderedDict()
        for expected_name, observatory in self._observatories.items():
            result = observatory.analyze(normalized_records, normalized_context)
            if not isinstance(result, ObservatoryResult):
                raise TypeError(
                    f"observatory {expected_name!r} returned "
                    f"{type(result).__name__}, expected ObservatoryResult."
                )
            if result.name != expected_name:
                raise ValueError(
                    f"observatory {expected_name!r} returned result name "
                    f"{result.name!r}."
                )
            results[expected_name] = result

        return MappingProxyType(results)

    @staticmethod
    def _validated_record(record: Mapping[str, Any], index: int) -> Mapping[str, Any]:
        if not isinstance(record, Mapping):
            raise TypeError(f"record {index} must be a mapping.")
        return MappingProxyType(dict(record))
