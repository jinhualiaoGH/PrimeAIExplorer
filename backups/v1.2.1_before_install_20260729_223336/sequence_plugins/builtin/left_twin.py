from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from plugins.left_twin import (
    build_left_twin_dataset,
    is_left_twin,
    load_left_twin_values,
    validate_left_twin_dataset,
    validate_source_repository,
)
from sequence_plugins.base import DatasetMetadata, SequencePlugin, sha256_file


class LeftTwinSequencePlugin(SequencePlugin):
    """Adapter over the stable EXP-000002 v1.1.1 implementation."""

    plugin_id = "left_twin"
    plugin_version = "1.2.0"
    display_name = "Left Twin Primes"
    supported_representations = ("absolute", "gaps", "combined")

    def validate_source(
        self,
        source: Path,
        *,
        required_count: int | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        count = required_count
        if count is None:
            count = int((options or {}).get("target_count", 1))
        return validate_source_repository(
            source,
            required_count=count,
        )

    def build_dataset(
        self,
        source: Path,
        destination: Path,
        *,
        count: int,
        options: Mapping[str, Any] | None = None,
    ) -> DatasetMetadata:
        result = build_left_twin_dataset(
            source,
            destination,
            target_count=count,
        )
        values = self.load_values(destination)
        return DatasetMetadata(
            plugin_id=self.plugin_id,
            plugin_version=self.plugin_version,
            count=len(values),
            dtype=str(getattr(values, "dtype", "uint64")),
            representation="absolute",
            source=str(source),
            sha256=sha256_file(destination),
            minimum=int(values[0]),
            maximum=int(values[-1]),
        )

    def load_values(
        self,
        dataset: Path,
        *,
        mmap_mode: str | None = "r",
    ) -> Sequence[int]:
        return load_left_twin_values(dataset, mmap_mode=mmap_mode)

    def validate_dataset(
        self,
        dataset: Path,
        *,
        representation: str = "absolute",
    ) -> dict[str, Any]:
        self.validate_representation(representation)
        result = validate_left_twin_dataset(dataset)
        result["plugin_id"] = self.plugin_id
        result["plugin_version"] = self.plugin_version
        result["representation"] = representation
        return result

    def is_structurally_valid(self, value: int) -> bool:
        return is_left_twin(value)
