from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import re

import numpy as np

from plugins.left_twin import is_prime_64
from sequence_plugins.base import DatasetMetadata, SequencePlugin

_PARTITION_RE = re.compile(r"^primes_(?P<start>\d+)_(?P<end>\d+)\.npy$", re.I)


@dataclass(frozen=True)
class PrimePartition:
    path: Path
    start: int
    end: int
    count: int
    dtype: str
    first_prime: int
    last_prime: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(value: str | Path, experiment_root: Path | None) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() and experiment_root is not None:
        path = experiment_root / path
    return path.resolve()


class PrimeValueSequencePlugin(SequencePlugin):
    """Phase A PrimeNet-backed consecutive-prime sequence plugin."""

    plugin_id = "prime_value"
    plugin_version = "1.3.0"
    display_name = "Prime Values"
    supported_representations = ("absolute",)

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self._config = dict(config) if config is not None else None

    def configure(self, config: Mapping[str, Any]) -> "PrimeValueSequencePlugin":
        self._config = dict(config)
        return self

    def _configuration(self, options: Mapping[str, Any] | None = None) -> dict[str, Any]:
        config = dict(options) if options is not None else self._config
        if config is None:
            raise ValueError("PrimeValueSequencePlugin requires the complete EXP-000003 configuration.")
        return config

    @staticmethod
    def _experiment_root(config: Mapping[str, Any]) -> Path | None:
        raw = config.get("_experiment_root")
        return Path(raw).resolve() if raw else None

    def _prime_root(self, source: Path, config: Mapping[str, Any]) -> Path:
        configured = config.get("repository", {}).get("prime_root")
        if configured:
            return _resolve(configured, self._experiment_root(config))
        return Path(source).expanduser().resolve()

    @staticmethod
    def _required_count(required_count: int | None, config: Mapping[str, Any]) -> int:
        count = int(required_count if required_count is not None else config.get("sequence", {}).get("target_count", 0))
        if count <= 0:
            raise ValueError("Required prime count must be positive.")
        return count

    def discover_partitions(self, prime_root: Path) -> list[tuple[Path, int, int]]:
        if not prime_root.exists():
            raise FileNotFoundError(f"Prime root does not exist: {prime_root}")
        if not prime_root.is_dir():
            raise NotADirectoryError(f"Prime root is not a directory: {prime_root}")
        records: list[tuple[Path, int, int]] = []
        for path in prime_root.iterdir():
            if path.is_file() and (match := _PARTITION_RE.fullmatch(path.name)):
                start, end = int(match.group("start")), int(match.group("end"))
                if start > end:
                    raise ValueError(f"Invalid partition range: {path.name}")
                records.append((path, start, end))
        records.sort(key=lambda item: (item[1], item[2], item[0].name.casefold()))
        if not records:
            raise ValueError(f"No canonical primes_START_END.npy partitions found: {prime_root}")
        ranges = [(start, end) for _, start, end in records]
        if len(ranges) != len(set(ranges)):
            raise ValueError("Duplicate PrimeNet partition range detected.")
        return records

    @staticmethod
    def validate_partition_adjacency(records: Sequence[tuple[Path, int, int]]) -> None:
        for previous, current in zip(records, records[1:]):
            if current[1] != previous[2] + 1:
                raise ValueError(
                    "PrimeNet partition adjacency failure: "
                    f"{previous[0].name} ends at {previous[2]:,}; "
                    f"{current[0].name} starts at {current[1]:,}; expected {previous[2] + 1:,}."
                )

    @staticmethod
    def inspect_partition(path: Path, start: int, end: int, full_check: bool) -> PrimePartition:
        values = np.load(path, mmap_mode="r", allow_pickle=False)
        if values.ndim != 1:
            raise ValueError(f"Prime partition is not one-dimensional: {path}")
        if values.dtype.kind != "u":
            raise ValueError(f"Prime partition must use unsigned integer dtype: {path} ({values.dtype})")
        if len(values) == 0:
            raise ValueError(f"Prime partition is empty: {path}")
        first, last = int(values[0]), int(values[-1])
        if not start <= first <= end or not start <= last <= end:
            raise ValueError(f"Prime value is outside filename range: {path.name}")
        if full_check and len(values) > 1 and not bool(np.all(values[1:] > values[:-1])):
            raise ValueError(f"Prime partition is not strictly increasing: {path}")
        return PrimePartition(path, start, end, int(len(values)), str(values.dtype), first, last)

    def validate_source(
        self,
        source: Path,
        *,
        required_count: int | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        config = self._configuration(options)
        prime_root = self._prime_root(source, config)
        required = self._required_count(required_count, config)
        full_check = bool(config.get("validation", {}).get("full_partition_monotonic_check", False))
        records = self.discover_partitions(prime_root)
        self.validate_partition_adjacency(records)

        partitions: list[PrimePartition] = []
        previous_last: int | None = None
        for path, start, end in records:
            partition = self.inspect_partition(path, start, end, full_check)
            if previous_last is not None and partition.first_prime <= previous_last:
                raise ValueError(f"Prime values are not strictly increasing across partition boundary before {path.name}.")
            partitions.append(partition)
            previous_last = partition.last_prime

        available = sum(partition.count for partition in partitions)
        manifest_raw = config.get("repository", {}).get("manifest")
        manifest = _resolve(manifest_raw, self._experiment_root(config)) if manifest_raw else None
        manifest_hash = _sha256(manifest) if manifest and manifest.is_file() else None
        return {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "source_type": "primenet_prime_repository",
            "prime_root": str(prime_root),
            "partition_count": len(partitions),
            "available_prime_count": available,
            "required_prime_count": required,
            "sufficient": available >= required,
            "first_prime": partitions[0].first_prime,
            "last_available_prime": partitions[-1].last_prime,
            "first_partition": partitions[0].path.name,
            "last_partition": partitions[-1].path.name,
            "source_manifest": str(manifest) if manifest else None,
            "source_manifest_exists": bool(manifest and manifest.is_file()),
            "source_manifest_sha256": manifest_hash,
            "full_partition_monotonic_check": full_check,
            "read_only": True,
            "valid": True,
        }

    def build_dataset(self, source: Path, destination: Path, *, count: int, options: Mapping[str, Any] | None = None) -> DatasetMetadata:
        raise NotImplementedError("Prime Value dataset construction is intentionally deferred to PrimeAIExplorer v1.3 Phase B.")

    def load_values(self, dataset: Path, *, mmap_mode: str | None = "r") -> Sequence[int]:
        values = np.load(dataset, mmap_mode=mmap_mode, allow_pickle=False)
        if values.ndim != 1:
            raise ValueError(f"Expected one-dimensional Prime Value dataset: {dataset}")
        return values

    def validate_dataset(self, dataset: Path, *, representation: str = "absolute") -> dict[str, Any]:
        raise NotImplementedError("Prime Value dataset validation is intentionally deferred to PrimeAIExplorer v1.3 Phase B.")

    def is_structurally_valid(self, value: int) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value > 1 and is_prime_64(value)
