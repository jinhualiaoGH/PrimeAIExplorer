from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from core.config import resolve_experiment_path
from core.io import pair_partitions
from core.models import SequenceWindow
from core.plugin import SequencePlugin


class PrimeGapPlugin(SequencePlugin):
    plugin_name = "prime_gap"
    display_name = "Prime Gap"
    definition = "A prime gap is the difference between two consecutive primes."

    def validate_source(self) -> dict[str, Any]:
        pairs = pair_partitions(
            self.config["repository"]["prime_root"],
            self.config["repository"]["gap_root"],
        )
        count = 0
        for prime_file, gap_file in pairs:
            primes = np.load(prime_file, mmap_mode="r")
            gaps = np.load(gap_file, mmap_mode="r")
            if len(primes) != len(gaps):
                raise ValueError(f"Length mismatch: {prime_file.name}, {gap_file.name}")
            count += len(gaps)
        return {"partitions": len(pairs), "gap_count": count}

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
            tmp, mode="w+", dtype=np.uint16, shape=(target_count,)
        )

        written = 0
        for _, gap_file in pairs:
            gaps = np.load(gap_file, mmap_mode="r")
            take = min(target_count - written, len(gaps))
            if take <= 0:
                break
            out[written : written + take] = gaps[:take]
            written += take

        out.flush()
        del out
        if written != target_count:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"Requested {target_count:,} gaps, found {written:,}")

        if destination.exists():
            destination.unlink()
        tmp.replace(destination)
        return destination

    def load_dataset(self) -> np.ndarray:
        path = resolve_experiment_path(
            self.config, self.config["sequence"]["dataset_file"]
        )
        return np.load(path, mmap_mode="r")

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

        if representation not in {"absolute", "gaps", "combined"}:
            raise ValueError("Prime-gap plugin supports absolute/gaps/combined aliases.")

        observed = [int(x) for x in data[endpoint0 - window_size + 1 : endpoint0 + 1]]
        return SequenceWindow(
            endpoint_index_1_based=endpoint_index_1_based,
            target_index_1_based=endpoint_index_1_based + 1,
            window_size=window_size,
            representation=representation,
            observed=observed,
            current_value=None,
            target_value=int(data[target0]),
        )
