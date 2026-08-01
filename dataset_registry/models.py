"""Immutable dataset and provenance models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DatasetArtifact:
    relative_path: str
    sha256: str
    size_bytes: int
    media_type: str = "application/octet-stream"
    record_count: int | None = None

    def __post_init__(self) -> None:
        if not self.relative_path or self.relative_path.startswith(("/", "\\")):
            raise ValueError("relative_path must be a non-empty relative path.")
        if len(self.sha256) != 64:
            raise ValueError("sha256 must contain 64 hexadecimal characters.")
        int(self.sha256, 16)
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative.")
        if self.record_count is not None and self.record_count < 0:
            raise ValueError("record_count must be non-negative.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DatasetSplit:
    name: str
    artifact_paths: tuple[str, ...]
    purpose: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("split name must not be empty.")
        if not self.artifact_paths:
            raise ValueError("split must contain at least one artifact path.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    source_type: str
    source_reference: str
    generated_by: str
    generated_at_utc: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    parent_dataset_ids: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.source_type.strip():
            raise ValueError("source_type must not be empty.")
        if not self.source_reference.strip():
            raise ValueError("source_reference must not be empty.")
        if not self.generated_by.strip():
            raise ValueError("generated_by must not be empty.")
        if not self.generated_at_utc.endswith("Z"):
            raise ValueError("generated_at_utc must be UTC and end with 'Z'.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    dataset_id: str
    name: str
    version: str
    description: str
    sequence_type: str
    schema_version: str
    artifacts: tuple[DatasetArtifact, ...]
    provenance: ProvenanceRecord
    splits: tuple[DatasetSplit, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.dataset_id.startswith("DS-"):
            raise ValueError("dataset_id must begin with 'DS-'.")
        if not self.name.strip():
            raise ValueError("name must not be empty.")
        if not self.version.strip():
            raise ValueError("version must not be empty.")
        if not self.sequence_type.strip():
            raise ValueError("sequence_type must not be empty.")
        if not self.artifacts:
            raise ValueError("manifest must contain at least one artifact.")

        paths = [item.relative_path for item in self.artifacts]
        if len(paths) != len(set(paths)):
            raise ValueError("artifact relative paths must be unique.")

        artifact_set = set(paths)
        for split in self.splits:
            missing = set(split.artifact_paths) - artifact_set
            if missing:
                raise ValueError(
                    f"split '{split.name}' references missing artifacts: "
                    + ", ".join(sorted(missing))
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "sequence_type": self.sequence_type,
            "schema_version": self.schema_version,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "provenance": self.provenance.to_dict(),
            "splits": [item.to_dict() for item in self.splits],
            "metadata": dict(self.metadata),
        }
