from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from kernel.exceptions import ValidationError

from .contracts import DatasetSpec
from .identity import canonical_metadata
from .suite_identity import registry_entry_identity
from .validation import require_text


@dataclass(frozen=True, slots=True)
class DatasetDescriptor:
    dataset_id: str
    version: str
    uri: str
    format: str
    split: str = "default"
    record_count: int | None = None
    content_sha256: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_id", require_text("dataset_id", self.dataset_id))
        object.__setattr__(self, "version", require_text("version", self.version))
        object.__setattr__(self, "uri", require_text("uri", self.uri))
        object.__setattr__(self, "format", require_text("format", self.format))
        object.__setattr__(self, "split", require_text("split", self.split))

        if self.record_count is not None:
            if (
                isinstance(self.record_count, bool)
                or not isinstance(self.record_count, int)
                or self.record_count < 0
            ):
                raise ValidationError("record_count must be a non-negative integer or None.")

        if self.content_sha256 is not None:
            digest = require_text("content_sha256", self.content_sha256).lower()
            if len(digest) != 64:
                raise ValidationError("content_sha256 must be 64 hex characters.")
            try:
                int(digest, 16)
            except ValueError as exc:
                raise ValidationError("content_sha256 must be hexadecimal.") from exc
            object.__setattr__(self, "content_sha256", digest)

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.dataset_id, self.version, self.split)

    @property
    def registry_id(self) -> str:
        return f"{self.dataset_id}@{self.version}#{self.split}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "uri": self.uri,
            "format": self.format,
            "split": self.split,
            "record_count": self.record_count,
            "content_sha256": self.content_sha256,
            "metadata": dict(self.metadata),
        }

    @property
    def descriptor_sha256(self) -> str:
        return registry_entry_identity(
            kind="dataset",
            entry_id=self.dataset_id,
            version=self.version,
            payload=self.identity_payload(),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["descriptor_sha256"] = self.descriptor_sha256
        return payload

    def to_dataset_spec(
        self,
        *,
        selector: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> DatasetSpec:
        merged_metadata = dict(self.metadata)
        merged_metadata.update(dict(metadata or {}))
        merged_metadata["descriptor_sha256"] = self.descriptor_sha256
        merged_metadata["uri"] = self.uri
        merged_metadata["format"] = self.format
        if self.record_count is not None:
            merged_metadata["record_count"] = self.record_count
        if self.content_sha256 is not None:
            merged_metadata["content_sha256"] = self.content_sha256

        return DatasetSpec(
            dataset_id=self.dataset_id,
            version=self.version,
            split=self.split,
            selector=dict(selector or {}),
            metadata=merged_metadata,
        )


class DatasetRegistry:
    def __init__(self, descriptors: Iterable[DatasetDescriptor] = ()) -> None:
        self._items: dict[tuple[str, str, str], DatasetDescriptor] = {}
        for descriptor in descriptors:
            self.register(descriptor)

    def register(self, descriptor: DatasetDescriptor) -> DatasetDescriptor:
        if not isinstance(descriptor, DatasetDescriptor):
            raise ValidationError("descriptor must be DatasetDescriptor.")
        existing = self._items.get(descriptor.key)
        if existing is None:
            self._items[descriptor.key] = descriptor
            return descriptor
        if existing == descriptor:
            return existing
        raise ValidationError(
            f"dataset registry conflict for {descriptor.registry_id}."
        )

    def get(self, dataset_id: str, version: str, split: str = "default") -> DatasetDescriptor:
        key = (
            require_text("dataset_id", dataset_id),
            require_text("version", version),
            require_text("split", split),
        )
        try:
            return self._items[key]
        except KeyError as exc:
            raise KeyError(f"dataset not registered: {dataset_id}@{version}#{split}") from exc

    def contains(self, dataset_id: str, version: str, split: str = "default") -> bool:
        return (dataset_id, version, split) in self._items

    def items(self) -> tuple[DatasetDescriptor, ...]:
        return tuple(
            self._items[key]
            for key in sorted(self._items)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h2.0",
            "datasets": [item.to_dict() for item in self.items()],
        }
