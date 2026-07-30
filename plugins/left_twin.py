from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from core.config import resolve_experiment_path
from core.io import pair_partitions
from core.models import SequenceWindow
from core.plugin import SequencePlugin


def is_probable_prime_64(n: int) -> bool:
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small:
        if n == p:
            return True
        if n % p == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    for a in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


class LeftTwinPlugin(SequencePlugin):
    plugin_name = "left_twin"
    display_name = "Left Twin Prime"
    definition = (
        "A left twin prime is a prime q such that q + 2 is also prime. "
        "ltp(i) denotes the i-th left twin prime."
    )

    def validate_source(self) -> dict[str, Any]:
        pairs = pair_partitions(
            self.config["repository"]["prime_root"],
            self.config["repository"]["gap_root"],
        )
        total = 0
        for prime_file, gap_file in pairs:
            primes = np.load(prime_file, mmap_mode="r")
            gaps = np.load(gap_file, mmap_mode="r")
            if len(primes) != len(gaps):
                raise ValueError(f"Length mismatch: {prime_file.name}, {gap_file.name}")
            total += int(np.count_nonzero(gaps == 2))
        return {"partitions": len(pairs), "left_twin_count": total}

    def build_dataset(self, overwrite: bool = False) -> Path:
        destination = resolve_experiment_path(
            self.config, self.config["sequence"]["dataset_file"]
        )
        if destination.exists() and not overwrite:
            return destination

        pairs = pair_partitions(
            self.config["repository"]["prime_root"],
            self.config["repository"]["gap_root"],
        )
        target_count = int(self.config["sequence"]["target_count"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        tmp = destination.with_suffix(destination.suffix + ".tmp")
        out = np.lib.format.open_memmap(
            tmp, mode="w+", dtype=np.uint64, shape=(target_count,)
        )

        written = 0
        for index, (prime_file, gap_file) in enumerate(pairs, start=1):
            primes = np.load(prime_file, mmap_mode="r")
            gaps = np.load(gap_file, mmap_mode="r")
            indices = np.flatnonzero(gaps == 2)
            take = min(target_count - written, len(indices))
            if take <= 0:
                break
            out[written : written + take] = np.asarray(
                primes[indices[:take]], dtype=np.uint64
            )
            written += take
            print(
                f"[{index:03d}/{len(pairs):03d}] "
                f"left_twins={len(indices):,} cumulative={written:,}/{target_count:,}"
            )

        out.flush()
        del out
        if written != target_count:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(
                f"Requested {target_count:,} left twin primes, found {written:,}"
            )

        if destination.exists():
            destination.unlink()
        tmp.replace(destination)
        return destination

    def load_dataset(self) -> np.ndarray:
        path = resolve_experiment_path(
            self.config, self.config["sequence"]["dataset_file"]
        )
        data = np.load(path, mmap_mode="r")
        if data.dtype != np.uint64:
            raise TypeError(f"Expected uint64, found {data.dtype}")
        return data

    def make_window(
        self,
        endpoint_index_1_based: int,
        window_size: int,
        representation: str,
    ) -> SequenceWindow:
        data = self.load_dataset()
        endpoint0 = endpoint_index_1_based - 1
        target0 = endpoint0 + 1
        if target0 >= len(data):
            raise IndexError("Target exceeds dataset.")

        if representation == "absolute":
            observed = [
                int(x)
                for x in data[endpoint0 - window_size + 1 : endpoint0 + 1]
            ]
            current = int(data[endpoint0])
        elif representation in {"gaps", "combined"}:
            source = np.asarray(
                data[endpoint0 - window_size : endpoint0 + 1], dtype=np.int64
            )
            observed = [int(x) for x in np.diff(source)]
            current = int(data[endpoint0]) if representation == "combined" else None
        else:
            raise ValueError(f"Unsupported representation: {representation}")

        return SequenceWindow(
            endpoint_index_1_based=endpoint_index_1_based,
            target_index_1_based=endpoint_index_1_based + 1,
            window_size=window_size,
            representation=representation,
            observed=observed,
            current_value=current,
            target_value=int(data[target0]),
        )

    def structural_validity(self, prediction: int) -> bool:
        return is_probable_prime_64(prediction) and is_probable_prime_64(prediction + 2)
