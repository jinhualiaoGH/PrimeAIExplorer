from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from kernel.context import ExecutionContext
from kernel.exceptions import ValidationError
from sequence_api.models import (
    SequenceDescriptor,
    SequenceValueType,
    SequenceWindow,
    SequenceWindowRequest,
    validate_value,
)


@dataclass(frozen=True)
class InMemorySequenceProvider:
    sequence_id: str
    values: tuple[int | float, ...]
    title: str = "In-memory sequence"
    sequence_version: str = "1.0.0"
    value_type: SequenceValueType = SequenceValueType.INTEGER
    index_origin: int = 0
    strictly_increasing: bool = False
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.sequence_id, str):
            raise ValidationError(
                "sequence_id must be text."
            )
        normalized_id = self.sequence_id.strip()
        if not normalized_id:
            raise ValidationError(
                "sequence_id must not be empty."
            )
        object.__setattr__(self, "sequence_id", normalized_id)
        if not isinstance(self.values, tuple):
            object.__setattr__(
                self,
                "values",
                tuple(self.values),
            )
        if not self.values:
            raise ValidationError(
                "In-memory sequence must contain values."
            )
        if not isinstance(self.value_type, SequenceValueType):
            object.__setattr__(
                self,
                "value_type",
                SequenceValueType(self.value_type),
            )
        validated = tuple(
            validate_value(value, self.value_type)
            for value in self.values
        )
        if self.strictly_increasing and any(
            left >= right
            for left, right in zip(validated, validated[1:])
        ):
            raise ValidationError(
                "Values are not strictly increasing."
            )
        object.__setattr__(self, "values", validated)
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata or {}),
        )

    @classmethod
    def from_configuration(
        cls,
        configuration: Mapping[str, Any],
    ) -> "InMemorySequenceProvider":
        if not isinstance(configuration, Mapping):
            raise ValidationError(
                "Provider configuration must be a mapping."
            )
        return cls(
            sequence_id=configuration["sequence_id"],
            values=tuple(configuration["values"]),
            title=configuration.get(
                "title",
                "In-memory sequence",
            ),
            sequence_version=configuration.get(
                "sequence_version",
                "1.0.0",
            ),
            value_type=SequenceValueType(
                configuration.get("value_type", "integer")
            ),
            index_origin=configuration.get("index_origin", 0),
            strictly_increasing=configuration.get(
                "strictly_increasing",
                False,
            ),
            metadata=configuration.get("metadata", {}),
        )

    def describe(
        self,
        context: ExecutionContext,
    ) -> SequenceDescriptor:
        return SequenceDescriptor(
            schema_version="1.0",
            sequence_id=self.sequence_id,
            sequence_version=self.sequence_version,
            title=self.title,
            value_type=self.value_type,
            index_origin=self.index_origin,
            finite=True,
            length=len(self.values),
            strictly_increasing=self.strictly_increasing,
            metadata={
                **dict(self.metadata or {}),
                "provider": type(self).__name__,
            },
        )

    def read_window(
        self,
        request: SequenceWindowRequest,
        context: ExecutionContext,
    ) -> SequenceWindow:
        if request.sequence_id != self.sequence_id:
            raise ValidationError(
                "Window request sequence_id does not match provider."
            )
        offset = request.start_index - self.index_origin
        if offset < 0:
            raise ValidationError(
                "Window begins before the sequence index origin."
            )
        end = offset + request.count
        if end > len(self.values):
            raise ValidationError(
                "Window exceeds the finite sequence boundary."
            )
        descriptor = self.describe(context)
        return SequenceWindow(
            descriptor_sha256=descriptor.descriptor_sha256,
            sequence_id=self.sequence_id,
            start_index=request.start_index,
            values=self.values[offset:end],
            value_type=self.value_type,
        )
