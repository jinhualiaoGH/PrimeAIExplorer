from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json

from kernel.exceptions import ConfigurationError, ValidationError
from kernel.serialization import stable_sha256


@dataclass(frozen=True)
class GapPartition:
    ordinal: int
    start_index: int
    count: int
    path: str
    sha256: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int):
            raise ValidationError("partition ordinal must be an integer.")
        if self.ordinal < 0:
            raise ValidationError("partition ordinal must be nonnegative.")
        if isinstance(self.start_index, bool) or not isinstance(
            self.start_index, int
        ):
            raise ValidationError("partition start_index must be an integer.")
        if isinstance(self.count, bool) or not isinstance(self.count, int):
            raise ValidationError("partition count must be an integer.")
        if self.count <= 0:
            raise ValidationError("partition count must be positive.")
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValidationError("partition path must not be empty.")
        if self.sha256 is not None and len(self.sha256.strip()) != 64:
            raise ValidationError("partition sha256 must contain 64 characters.")

    @property
    def end_index(self) -> int:
        return self.start_index + self.count - 1

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ordinal": self.ordinal,
            "start_index": self.start_index,
            "count": self.count,
            "path": self.path,
        }
        if self.sha256 is not None:
            payload["sha256"] = self.sha256.lower()
        return payload


@dataclass(frozen=True)
class GapRepositoryManifest:
    schema_version: str
    repository_id: str
    repository_version: str
    dtype: str
    index_origin: int
    partitions: tuple[GapPartition, ...]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise ValidationError("unsupported gap manifest schema version.")
        if not self.repository_id.strip():
            raise ValidationError("repository_id must not be empty.")
        if not self.repository_version.strip():
            raise ValidationError("repository_version must not be empty.")
        if self.dtype not in {"uint16", "<u2", "|u2"}:
            raise ValidationError("gap repository dtype must be uint16.")
        if not self.partitions:
            raise ValidationError("gap manifest must contain partitions.")
        ordered = tuple(sorted(self.partitions, key=lambda item: item.ordinal))
        if ordered != self.partitions:
            raise ValidationError("partitions must be ordered by ordinal.")
        expected_start = self.index_origin
        for expected_ordinal, partition in enumerate(self.partitions):
            if partition.ordinal != expected_ordinal:
                raise ValidationError("partition ordinals must be contiguous.")
            if partition.start_index != expected_start:
                raise ValidationError("partition index ranges must be contiguous.")
            expected_start = partition.end_index + 1

    @property
    def length(self) -> int:
        return sum(partition.count for partition in self.partitions)

    @property
    def end_index(self) -> int:
        return self.index_origin + self.length - 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository_id": self.repository_id,
            "repository_version": self.repository_version,
            "dtype": "uint16",
            "index_origin": self.index_origin,
            "partitions": [item.to_dict() for item in self.partitions],
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return stable_sha256(self.to_dict())

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GapRepositoryManifest":
        if not isinstance(payload, Mapping):
            raise ValidationError("gap manifest must be a mapping.")
        required = {
            "schema_version",
            "repository_id",
            "repository_version",
            "dtype",
            "index_origin",
            "partitions",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(f"gap manifest is missing fields: {missing}")
        raw_partitions = payload["partitions"]
        if not isinstance(raw_partitions, Sequence) or isinstance(
            raw_partitions, (str, bytes)
        ):
            raise ValidationError("partitions must be a sequence.")
        partitions = tuple(
            GapPartition(
                ordinal=item["ordinal"],
                start_index=item["start_index"],
                count=item["count"],
                path=item["path"],
                sha256=item.get("sha256"),
            )
            for item in raw_partitions
        )
        return cls(
            schema_version=payload["schema_version"],
            repository_id=payload["repository_id"],
            repository_version=payload["repository_version"],
            dtype=payload["dtype"],
            index_origin=payload["index_origin"],
            partitions=partitions,
            metadata=payload.get("metadata", {}),
        )

    @classmethod
    def load(cls, path: Path) -> "GapRepositoryManifest":
        if not path.is_file():
            raise ConfigurationError(f"gap manifest does not exist: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ConfigurationError(f"could not read gap manifest: {path}") from exc
        return cls.from_mapping(payload)
