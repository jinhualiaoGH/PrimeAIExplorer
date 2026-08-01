from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any, Iterable, Mapping

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256


class SequenceValueType(str, Enum):
    INTEGER = "integer"
    REAL = "real"


def _required_text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be text.")
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"{name} must not be empty.")
    return normalized


def _positive_integer(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer.")
    if value <= 0:
        raise ValidationError(f"{name} must be positive.")
    return value


def validate_value(
    value: Any,
    value_type: SequenceValueType,
) -> int | float:
    if value_type is SequenceValueType.INTEGER:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError(
                "Integer sequence values must be integers."
            )
        return value

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(
            "Real sequence values must be finite numbers."
        )
    normalized = float(value)
    if not isfinite(normalized):
        raise ValidationError(
            "Real sequence values must be finite numbers."
        )
    return normalized


@dataclass(frozen=True)
class SequenceDescriptor:
    schema_version: str
    sequence_id: str
    sequence_version: str
    title: str
    value_type: SequenceValueType
    index_origin: int
    finite: bool
    length: int | None
    strictly_increasing: bool
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _required_text("schema_version", self.schema_version),
        )
        object.__setattr__(
            self,
            "sequence_id",
            _required_text("sequence_id", self.sequence_id),
        )
        object.__setattr__(
            self,
            "sequence_version",
            _required_text(
                "sequence_version",
                self.sequence_version,
            ),
        )
        object.__setattr__(
            self,
            "title",
            _required_text("title", self.title),
        )
        if not isinstance(self.value_type, SequenceValueType):
            object.__setattr__(
                self,
                "value_type",
                SequenceValueType(self.value_type),
            )
        if isinstance(self.index_origin, bool) or not isinstance(
            self.index_origin,
            int,
        ):
            raise ValidationError(
                "index_origin must be an integer."
            )
        if not isinstance(self.finite, bool):
            raise ValidationError("finite must be boolean.")
        if not isinstance(self.strictly_increasing, bool):
            raise ValidationError(
                "strictly_increasing must be boolean."
            )
        if self.length is not None:
            _positive_integer("length", self.length)
        if self.finite and self.length is None:
            raise ValidationError(
                "Finite sequences must declare length."
            )
        if not self.finite and self.length is not None:
            raise ValidationError(
                "Infinite sequences must not declare length."
            )
        if not isinstance(self.metadata, Mapping):
            raise ValidationError(
                "metadata must be a mapping."
            )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sequence_id": self.sequence_id,
            "sequence_version": self.sequence_version,
            "title": self.title,
            "value_type": self.value_type.value,
            "index_origin": self.index_origin,
            "finite": self.finite,
            "length": self.length,
            "strictly_increasing": self.strictly_increasing,
            "metadata": dict(self.metadata),
        }

    @property
    def descriptor_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class SequenceWindowRequest:
    sequence_id: str
    start_index: int
    count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sequence_id",
            _required_text("sequence_id", self.sequence_id),
        )
        if isinstance(self.start_index, bool) or not isinstance(
            self.start_index,
            int,
        ):
            raise ValidationError(
                "start_index must be an integer."
            )
        _positive_integer("count", self.count)

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
    ) -> "SequenceWindowRequest":
        if not isinstance(payload, Mapping):
            raise ValidationError(
                "Window request payload must be a mapping."
            )
        required = {"sequence_id", "start_index", "count"}
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(
                f"Window request is missing fields: {missing}"
            )
        return cls(
            sequence_id=payload["sequence_id"],
            start_index=payload["start_index"],
            count=payload["count"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "start_index": self.start_index,
            "count": self.count,
        }

    @property
    def request_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class SequenceWindow:
    descriptor_sha256: str
    sequence_id: str
    start_index: int
    values: tuple[int | float, ...]
    value_type: SequenceValueType

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "descriptor_sha256",
            _required_text(
                "descriptor_sha256",
                self.descriptor_sha256,
            ),
        )
        if len(self.descriptor_sha256) != 64:
            raise ValidationError(
                "descriptor_sha256 must contain 64 characters."
            )
        object.__setattr__(
            self,
            "sequence_id",
            _required_text("sequence_id", self.sequence_id),
        )
        if isinstance(self.start_index, bool) or not isinstance(
            self.start_index,
            int,
        ):
            raise ValidationError(
                "start_index must be an integer."
            )
        if not isinstance(self.value_type, SequenceValueType):
            object.__setattr__(
                self,
                "value_type",
                SequenceValueType(self.value_type),
            )
        if not isinstance(self.values, tuple):
            object.__setattr__(self, "values", tuple(self.values))
        validated = tuple(
            validate_value(value, self.value_type)
            for value in self.values
        )
        if not validated:
            raise ValidationError(
                "SequenceWindow must contain at least one value."
            )
        object.__setattr__(self, "values", validated)

    @property
    def end_index(self) -> int:
        return self.start_index + len(self.values) - 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "descriptor_sha256": self.descriptor_sha256,
            "sequence_id": self.sequence_id,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "count": len(self.values),
            "value_type": self.value_type.value,
            "values": list(self.values),
        }

    @property
    def window_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class SequenceBatchRequest:
    requests: tuple[SequenceWindowRequest, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.requests, tuple):
            object.__setattr__(
                self,
                "requests",
                tuple(self.requests),
            )
        if not self.requests:
            raise ValidationError(
                "SequenceBatchRequest must contain requests."
            )
        if not all(
            isinstance(request, SequenceWindowRequest)
            for request in self.requests
        ):
            raise ValidationError(
                "Batch entries must be SequenceWindowRequest values."
            )

    @classmethod
    def from_iterable(
        cls,
        requests: Iterable[SequenceWindowRequest],
    ) -> "SequenceBatchRequest":
        return cls(tuple(requests))

    def to_dict(self) -> dict[str, Any]:
        return {
            "requests": [
                request.to_dict() for request in self.requests
            ]
        }

    @property
    def request_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class SequenceBatch:
    windows: tuple[SequenceWindow, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.windows, tuple):
            object.__setattr__(
                self,
                "windows",
                tuple(self.windows),
            )
        if not self.windows:
            raise ValidationError(
                "SequenceBatch must contain windows."
            )
        if not all(
            isinstance(window, SequenceWindow)
            for window in self.windows
        ):
            raise ValidationError(
                "Batch entries must be SequenceWindow values."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "windows": [
                window.to_dict() for window in self.windows
            ]
        }

    @property
    def batch_sha256(self) -> str:
        return stable_sha256(self.to_dict())
