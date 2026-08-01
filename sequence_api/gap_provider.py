from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
import bisect
import gc

import numpy as np

from kernel.context import ExecutionContext
from kernel.exceptions import ConfigurationError, ValidationError
from sequence_api.file_identity import file_sha256
from sequence_api.gap_manifest import GapPartition, GapRepositoryManifest
from sequence_api.models import (
    SequenceDescriptor,
    SequenceValueType,
    SequenceWindow,
    SequenceWindowRequest,
)


@dataclass
class PartitionedGapSequenceProvider:
    sequence_id: str
    manifest_path: str
    title: str = "Partitioned prime-gap sequence"
    sequence_version: str = "1.0.0"
    cache_size: int = 2
    verify_partition_sha256: bool = False
    metadata: Mapping[str, Any] | None = None
    _manifest: GapRepositoryManifest | None = field(default=None, init=False, repr=False)
    _manifest_file: Path | None = field(default=None, init=False, repr=False)
    _cache: OrderedDict[int, np.memmap] = field(
        default_factory=OrderedDict, init=False, repr=False
    )

    provider_type = "partitioned_gap_uint16"

    def __post_init__(self) -> None:
        self.sequence_id = self.sequence_id.strip()
        self.manifest_path = self.manifest_path.strip()
        if not self.sequence_id:
            raise ValidationError("sequence_id must not be empty.")
        if not self.manifest_path:
            raise ValidationError("manifest_path must not be empty.")
        if isinstance(self.cache_size, bool) or not isinstance(self.cache_size, int):
            raise ValidationError("cache_size must be an integer.")
        if self.cache_size <= 0:
            raise ValidationError("cache_size must be positive.")
        if not isinstance(self.verify_partition_sha256, bool):
            raise ValidationError("verify_partition_sha256 must be boolean.")
        self.metadata = dict(self.metadata or {})

    @classmethod
    def from_configuration(
        cls, configuration: Mapping[str, Any]
    ) -> "PartitionedGapSequenceProvider":
        if not isinstance(configuration, Mapping):
            raise ValidationError("provider configuration must be a mapping.")
        missing = sorted({"sequence_id", "manifest_path"} - set(configuration))
        if missing:
            raise ValidationError(f"gap provider is missing fields: {missing}")
        return cls(
            sequence_id=configuration["sequence_id"],
            manifest_path=configuration["manifest_path"],
            title=configuration.get("title", "Partitioned prime-gap sequence"),
            sequence_version=configuration.get("sequence_version", "1.0.0"),
            cache_size=configuration.get("cache_size", 2),
            verify_partition_sha256=configuration.get(
                "verify_partition_sha256", False
            ),
            metadata=configuration.get("metadata", {}),
        )

    def _resolve_manifest_path(self, context: ExecutionContext) -> Path:
        candidate = Path(self.manifest_path).expanduser()
        if not candidate.is_absolute():
            candidate = Path(context.project_root) / candidate
        return candidate.resolve()

    def _load_manifest(self, context: ExecutionContext) -> GapRepositoryManifest:
        path = self._resolve_manifest_path(context)
        if self._manifest is not None:
            if path != self._manifest_file:
                raise ConfigurationError("manifest path changed after provider opened.")
            return self._manifest
        manifest = GapRepositoryManifest.load(path)
        self._manifest = manifest
        self._manifest_file = path
        return manifest

    def _partition_path(self, partition: GapPartition) -> Path:
        assert self._manifest_file is not None
        candidate = Path(partition.path).expanduser()
        if not candidate.is_absolute():
            candidate = self._manifest_file.parent / candidate
        return candidate.resolve()

    @staticmethod
    def _close_array(array: np.memmap) -> None:
        mapping = getattr(array, "_mmap", None)
        if mapping is not None and not mapping.closed:
            mapping.close()

    def _open_partition(self, partition: GapPartition) -> np.memmap:
        if partition.ordinal in self._cache:
            array = self._cache.pop(partition.ordinal)
            self._cache[partition.ordinal] = array
            return array
        path = self._partition_path(partition)
        if not path.is_file():
            raise ConfigurationError(f"gap partition does not exist: {path}")
        if path.suffix.lower() != ".npy":
            raise ConfigurationError("gap partitions must use .npy files.")
        try:
            array = np.load(path, mmap_mode="r", allow_pickle=False)
        except Exception as exc:
            raise ConfigurationError(f"could not memory-map gap partition: {path}") from exc
        if not isinstance(array, np.memmap):
            raise ConfigurationError("gap partition was not opened as a memory map.")
        if array.ndim != 1:
            self._close_array(array)
            raise ValidationError("gap partition must be one-dimensional.")
        if array.dtype != np.dtype("uint16"):
            self._close_array(array)
            raise ValidationError("gap partition dtype must be uint16.")
        if int(array.size) != partition.count:
            self._close_array(array)
            raise ValidationError("gap partition count does not match manifest.")
        if array.flags.writeable:
            self._close_array(array)
            raise ValidationError("gap partition must be read-only.")
        if self.verify_partition_sha256 and partition.sha256:
            if file_sha256(path) != partition.sha256.lower():
                self._close_array(array)
                raise ValidationError("gap partition SHA-256 does not match manifest.")
        self._cache[partition.ordinal] = array
        while len(self._cache) > self.cache_size:
            _, evicted = self._cache.popitem(last=False)
            self._close_array(evicted)
            del evicted
        return array

    @property
    def open_partition_count(self) -> int:
        return len(self._cache)

    def describe(self, context: ExecutionContext) -> SequenceDescriptor:
        manifest = self._load_manifest(context)
        return SequenceDescriptor(
            schema_version="1.0",
            sequence_id=self.sequence_id,
            sequence_version=self.sequence_version,
            title=self.title,
            value_type=SequenceValueType.INTEGER,
            index_origin=manifest.index_origin,
            finite=True,
            length=manifest.length,
            strictly_increasing=False,
            metadata={
                **dict(self.metadata or {}),
                "provider": type(self).__name__,
                "source_type": self.provider_type,
                "repository_id": manifest.repository_id,
                "repository_version": manifest.repository_version,
                "repository_dtype": "uint16",
                "partition_count": len(manifest.partitions),
                "manifest_sha256": manifest.manifest_sha256,
                "read_only": True,
                "memory_mapped": True,
                "cross_partition_windows": True,
                "cache_size": self.cache_size,
            },
        )

    def read_window(
        self,
        request: SequenceWindowRequest,
        context: ExecutionContext,
    ) -> SequenceWindow:
        if request.sequence_id != self.sequence_id:
            raise ValidationError("window sequence_id does not match provider.")
        manifest = self._load_manifest(context)
        if request.start_index < manifest.index_origin:
            raise ValidationError("window begins before repository index origin.")
        requested_end = request.start_index + request.count - 1
        if requested_end > manifest.end_index:
            raise ValidationError("window exceeds repository boundary.")

        starts = [partition.start_index for partition in manifest.partitions]
        ordinal = bisect.bisect_right(starts, request.start_index) - 1
        remaining = request.count
        cursor = request.start_index
        values: list[int] = []

        while remaining:
            partition = manifest.partitions[ordinal]
            array = self._open_partition(partition)
            local_start = cursor - partition.start_index
            available = partition.count - local_start
            take = min(remaining, available)
            values.extend(int(value) for value in array[local_start:local_start + take])
            remaining -= take
            cursor += take
            ordinal += 1

        descriptor = self.describe(context)
        return SequenceWindow(
            descriptor_sha256=descriptor.descriptor_sha256,
            sequence_id=self.sequence_id,
            start_index=request.start_index,
            values=tuple(values),
            value_type=SequenceValueType.INTEGER,
        )

    def close(self) -> None:
        arrays = list(self._cache.values())
        self._cache.clear()
        self._manifest = None
        self._manifest_file = None
        for array in arrays:
            self._close_array(array)
        arrays.clear()
        gc.collect()

    def __enter__(self) -> "PartitionedGapSequenceProvider":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
