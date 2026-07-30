from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

from core.config import resolve_experiment_path
from core.io import pair_partitions
from core.models import SequenceWindow
from core.plugin import SequencePlugin


_INITIAL_LEFT_TWINS = np.asarray(
    [3, 5, 11, 17, 29, 41, 59, 71, 101],
    dtype=np.uint64,
)


def is_prime_64(n: int) -> bool:
    """Deterministic Miller-Rabin primality test for unsigned 64-bit integers."""
    if n < 2:
        return False

    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small_primes:
        if n == prime:
            return True
        if n % prime == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    # Deterministic for n < 2^64.
    for base in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        if base % n == 0:
            continue
        value = pow(base, d, n)
        if value in (1, n - 1):
            continue
        for _ in range(s - 1):
            value = pow(value, 2, n)
            if value == n - 1:
                break
        else:
            return False
    return True


def _sha256(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


class LeftTwinPlugin(SequencePlugin):
    plugin_name = "left_twin"
    display_name = "Left Twin Prime"
    definition = (
        "A left twin prime is a prime q such that q + 2 is also prime. "
        "ltp(i) denotes the i-th left twin prime. The sequence includes 3 and 5."
    )
    plugin_version = "1.1.0"
    supported_representations = ("absolute", "gaps", "combined")

    def _dataset_path(self) -> Path:
        return resolve_experiment_path(
            self.config,
            self.config["sequence"]["dataset_file"],
        )

    def _metadata_path(self) -> Path:
        configured = self.config["sequence"].get(
            "metadata_file",
            "data/left_twin_primes.metadata.json",
        )
        return resolve_experiment_path(self.config, configured)

    def validate_source(self) -> dict[str, Any]:
        pairs = pair_partitions(
            self.config["repository"]["prime_root"],
            self.config["repository"]["gap_root"],
        )

        total_primes = 0
        total_left_twins = 0
        partition_records: list[dict[str, Any]] = []

        previous_last_prime: int | None = None
        for partition_index, (prime_file, gap_file) in enumerate(pairs, start=1):
            primes = np.load(prime_file, mmap_mode="r")
            gaps = np.load(gap_file, mmap_mode="r")

            if primes.ndim != 1 or gaps.ndim != 1:
                raise ValueError(
                    f"Expected one-dimensional arrays: "
                    f"{prime_file.name}, {gap_file.name}"
                )
            if len(primes) != len(gaps):
                raise ValueError(
                    f"Length mismatch: {prime_file.name}={len(primes):,}, "
                    f"{gap_file.name}={len(gaps):,}"
                )
            if not np.issubdtype(primes.dtype, np.integer):
                raise TypeError(f"Prime dtype is not integral: {primes.dtype}")
            if not np.issubdtype(gaps.dtype, np.integer):
                raise TypeError(f"Gap dtype is not integral: {gaps.dtype}")
            if len(primes) and previous_last_prime is not None:
                if int(primes[0]) <= previous_last_prime:
                    raise ValueError(
                        f"Prime partitions are not strictly ordered at "
                        f"{prime_file.name}"
                    )
            if len(primes):
                previous_last_prime = int(primes[-1])

            left_twins = int(np.count_nonzero(gaps == 2))
            total_primes += int(len(primes))
            total_left_twins += left_twins
            partition_records.append(
                {
                    "partition_index": partition_index,
                    "prime_file": prime_file.name,
                    "gap_file": gap_file.name,
                    "stored_primes": int(len(primes)),
                    "left_twin_primes": left_twins,
                }
            )

        return {
            "plugin": self.plugin_name,
            "plugin_version": self.plugin_version,
            "partitions": len(pairs),
            "stored_primes": total_primes,
            "left_twin_count": total_left_twins,
            "target_count": int(self.config["sequence"]["target_count"]),
            "sufficient": total_left_twins
            >= int(self.config["sequence"]["target_count"]),
            "partition_records": partition_records,
        }

    def build_dataset(self, overwrite: bool = False) -> Path:
        destination = self._dataset_path()
        metadata_path = self._metadata_path()
        target_count = int(self.config["sequence"]["target_count"])

        if target_count < 2:
            raise ValueError("target_count must be at least 2.")
        if destination.exists() and not overwrite:
            return destination

        destination.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.unlink(missing_ok=True)

        pairs = pair_partitions(
            self.config["repository"]["prime_root"],
            self.config["repository"]["gap_root"],
        )
        started = time.time()
        written = 0
        extraction_records: list[dict[str, Any]] = []

        output = np.lib.format.open_memmap(
            temporary,
            mode="w+",
            dtype=np.uint64,
            shape=(target_count,),
        )

        try:
            for partition_index, (prime_file, gap_file) in enumerate(
                pairs,
                start=1,
            ):
                primes = np.load(prime_file, mmap_mode="r")
                gaps = np.load(gap_file, mmap_mode="r")
                if len(primes) != len(gaps):
                    raise ValueError(
                        f"Length mismatch: {prime_file.name}, {gap_file.name}"
                    )

                indices = np.flatnonzero(gaps == 2)
                remaining = target_count - written
                take = min(remaining, int(len(indices)))

                if take:
                    output[written : written + take] = np.asarray(
                        primes[indices[:take]],
                        dtype=np.uint64,
                    )
                    written += take

                extraction_records.append(
                    {
                        "partition_index": partition_index,
                        "prime_file": prime_file.name,
                        "gap_file": gap_file.name,
                        "left_twins_found": int(len(indices)),
                        "left_twins_written": int(take),
                        "cumulative_written": int(written),
                    }
                )

                print(
                    f"[{partition_index:03d}/{len(pairs):03d}] "
                    f"left_twins={len(indices):,} "
                    f"cumulative={written:,}/{target_count:,}"
                )
                if written >= target_count:
                    break

            output.flush()
            del output

            if written != target_count:
                temporary.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Requested {target_count:,} left twin primes, "
                    f"but found only {written:,}."
                )

            if destination.exists():
                destination.unlink()
            os.replace(temporary, destination)

        except Exception:
            try:
                del output
            except Exception:
                pass
            temporary.unlink(missing_ok=True)
            raise

        validation = self.validate_dataset(destination)
        metadata = {
            "experiment_id": self.config["experiment"]["id"],
            "experiment_version": self.config["experiment"].get("version", "1.1.0"),
            "plugin": self.plugin_name,
            "plugin_version": self.plugin_version,
            "definition": self.definition,
            "index_base": 1,
            "dtype": "uint64",
            "count": target_count,
            "observation_count": target_count - 1,
            "held_out_target_index_1_based": target_count,
            "first_value": int(validation["first_value"]),
            "last_observed_value": int(validation["last_observed_value"]),
            "held_out_target_value": int(validation["held_out_target_value"]),
            "dataset_sha256": _sha256(destination),
            "elapsed_seconds": time.time() - started,
            "source_prime_root": self.config["repository"]["prime_root"],
            "source_gap_root": self.config["repository"]["gap_root"],
            "extraction_records": extraction_records,
        }
        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
        return destination

    def validate_dataset(self, path: Path | None = None) -> dict[str, Any]:
        dataset_path = path or self._dataset_path()
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        data = np.load(dataset_path, mmap_mode="r")
        if data.ndim != 1:
            raise ValueError("Left-twin dataset must be one-dimensional.")
        if data.dtype != np.uint64:
            raise TypeError(f"Expected uint64 dataset, found {data.dtype}.")
        if len(data) < 2:
            raise ValueError("Left-twin dataset must contain at least two values.")
        if np.any(data[1:] <= data[:-1]):
            raise ValueError("Left-twin dataset is not strictly increasing.")
        if np.any(data % 2 == 0):
            raise ValueError("Left-twin dataset contains an even value.")

        prefix_length = min(len(data), len(_INITIAL_LEFT_TWINS))
        if not np.array_equal(data[:prefix_length], _INITIAL_LEFT_TWINS[:prefix_length]):
            raise ValueError(
                "Canonical initial left-twin-prime sequence does not match."
            )

        return {
            "valid": True,
            "path": str(dataset_path),
            "dtype": str(data.dtype),
            "count": int(len(data)),
            "first_value": int(data[0]),
            "last_observed_value": int(data[-2]),
            "held_out_target_value": int(data[-1]),
        }

    def load_dataset(self) -> np.ndarray:
        path = self._dataset_path()
        self.validate_dataset(path)
        return np.load(path, mmap_mode="r")

    def make_window(
        self,
        endpoint_index_1_based: int,
        window_size: int,
        representation: str,
    ) -> SequenceWindow:
        if window_size < 1:
            raise ValueError("window_size must be positive.")
        if representation not in self.supported_representations:
            raise ValueError(
                f"Unsupported representation {representation!r}; "
                f"supported: {self.supported_representations}"
            )

        data = self.load_dataset()
        endpoint0 = endpoint_index_1_based - 1
        target0 = endpoint0 + 1

        if endpoint_index_1_based < 1:
            raise IndexError("Endpoint index must be positive.")
        if target0 >= len(data):
            raise IndexError(
                f"Target index {endpoint_index_1_based + 1:,} exceeds "
                f"dataset count {len(data):,}."
            )

        current = int(data[endpoint0])
        if representation == "absolute":
            start0 = endpoint0 - window_size + 1
            if start0 < 0:
                raise IndexError("Window extends before the start of the dataset.")
            observed = [int(x) for x in data[start0 : endpoint0 + 1]]
        else:
            start0 = endpoint0 - window_size
            if start0 < 0:
                raise IndexError("Gap window extends before the start of the dataset.")
            source = np.asarray(data[start0 : endpoint0 + 1], dtype=np.int64)
            observed = [int(x) for x in np.diff(source)]

        return SequenceWindow(
            endpoint_index_1_based=endpoint_index_1_based,
            target_index_1_based=endpoint_index_1_based + 1,
            window_size=window_size,
            representation=representation,
            observed=observed,
            current_value=current if representation in {"absolute", "combined"} else None,
            target_value=int(data[target0]),
        )

    def structural_validity(self, prediction: int) -> bool:
        return is_prime_64(prediction) and is_prime_64(prediction + 2)

    def metadata(self) -> dict[str, Any]:
        return {
            "plugin_name": self.plugin_name,
            "display_name": self.display_name,
            "plugin_version": self.plugin_version,
            "definition": self.definition,
            "supported_representations": list(self.supported_representations),
        }
