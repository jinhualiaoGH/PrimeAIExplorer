from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
import os
import tempfile

import numpy as np

from sequence_plugins.base import (
    DatasetMetadata,
    SequencePlugin,
    sha256_file,
)


class NumpyFileSequencePlugin(SequencePlugin):
    """Base plugin for canonical one-dimensional uint64 NumPy arrays."""

    dtype = np.dtype("<u8")

    def validate_source(
        self,
        source: Path,
        *,
        required_count: int | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not source.exists():
            return {
                "source": str(source),
                "exists": False,
                "count": 0,
                "sufficient": False,
            }
        values = np.load(source, mmap_mode="r", allow_pickle=False)
        if values.ndim != 1:
            raise ValueError(f"Expected one-dimensional array: {source}")
        count = int(values.shape[0])
        return {
            "source": str(source),
            "exists": True,
            "count": count,
            "sufficient": (
                required_count is None or count >= required_count
            ),
            "dtype": str(values.dtype),
        }

    def _source_values(
        self,
        source: Path,
        *,
        options: Mapping[str, Any] | None = None,
    ) -> Sequence[int]:
        return np.load(source, mmap_mode="r", allow_pickle=False)

    def build_dataset(
        self,
        source: Path,
        destination: Path,
        *,
        count: int,
        options: Mapping[str, Any] | None = None,
    ) -> DatasetMetadata:
        if count <= 0:
            raise ValueError("count must be positive.")

        source_values = self._source_values(source, options=options)
        if len(source_values) < count:
            raise ValueError(
                f"Source has {len(source_values)} values, requested {count}."
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp.npy",
            dir=destination.parent,
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            output = np.lib.format.open_memmap(
                temporary,
                mode="w+",
                dtype=self.dtype,
                shape=(count,),
            )
            output[:] = [
                self.transform_source_value(int(value), options=options)
                for value in source_values[:count]
            ]
            output.flush()
            del output
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        values = np.load(destination, mmap_mode="r", allow_pickle=False)
        return DatasetMetadata(
            plugin_id=self.plugin_id,
            plugin_version=self.plugin_version,
            count=count,
            dtype=str(values.dtype),
            representation="absolute",
            source=str(source),
            sha256=sha256_file(destination),
            minimum=int(values[0]),
            maximum=int(values[-1]),
        )

    def transform_source_value(
        self,
        value: int,
        *,
        options: Mapping[str, Any] | None = None,
    ) -> int:
        return value

    def load_values(
        self,
        dataset: Path,
        *,
        mmap_mode: str | None = "r",
    ) -> Sequence[int]:
        values = np.load(dataset, mmap_mode=mmap_mode, allow_pickle=False)
        if values.ndim != 1:
            raise ValueError(f"Expected one-dimensional array: {dataset}")
        return values
