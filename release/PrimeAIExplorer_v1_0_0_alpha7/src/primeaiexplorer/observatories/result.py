"""Validated result contract shared by all PrimeAIExplorer observatories."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


def _validated_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be empty.")
    return cleaned


def _mapping_copy(value: Mapping[str, Any], *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping.")
    return MappingProxyType(dict(value))


def _tables_copy(value: Mapping[str, Sequence[Mapping[str, Any]]]) -> Mapping[str, tuple[Mapping[str, Any], ...]]:
    if not isinstance(value, Mapping):
        raise TypeError("tables must be a mapping.")

    normalized: dict[str, tuple[Mapping[str, Any], ...]] = {}
    for table_name, rows in value.items():
        clean_name = _validated_text(table_name, field_name="table name")
        if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
            raise TypeError(f"table {clean_name!r} must be a sequence of mappings.")
        normalized_rows: list[Mapping[str, Any]] = []
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, Mapping):
                raise TypeError(
                    f"table {clean_name!r} row {index} must be a mapping."
                )
            normalized_rows.append(MappingProxyType(dict(row)))
        normalized[clean_name] = tuple(normalized_rows)
    return MappingProxyType(normalized)


def _warnings_copy(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("warnings must be a sequence of strings.")
    return tuple(
        _validated_text(item, field_name="warning")
        for item in value
    )


@dataclass(frozen=True, slots=True)
class ObservatoryResult:
    """Standard, validated in-memory result returned by an observatory."""

    name: str
    version: str = "1.0.0"
    summary: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, Any] = field(default_factory=dict)
    tables: Mapping[str, Sequence[Mapping[str, Any]]] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    warnings: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _validated_text(self.name, field_name="name"))
        object.__setattr__(self, "version", _validated_text(self.version, field_name="version"))
        object.__setattr__(self, "summary", _mapping_copy(self.summary, field_name="summary"))
        object.__setattr__(self, "metrics", _mapping_copy(self.metrics, field_name="metrics"))
        object.__setattr__(self, "tables", _tables_copy(self.tables))
        object.__setattr__(self, "metadata", _mapping_copy(self.metadata, field_name="metadata"))
        object.__setattr__(self, "warnings", _warnings_copy(self.warnings))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable shallow representation."""

        return {
            "name": self.name,
            "version": self.version,
            "summary": dict(self.summary),
            "metrics": dict(self.metrics),
            "tables": {
                name: [dict(row) for row in rows]
                for name, rows in self.tables.items()
            },
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
        }
