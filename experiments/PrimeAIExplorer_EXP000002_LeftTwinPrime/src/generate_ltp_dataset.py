from __future__ import annotations

import argparse
import hashlib
import os
import time
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap

from common import (
    ensure_directories,
    load_config,
    pair_partitions,
    resolve_output,
    write_json,
)


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract left twin primes from aligned PrimeNet prime/gap partitions."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    ensure_directories(config)

    target_count = int(config["target_count"])
    output_path = resolve_output(config, config["dataset_file"])
    metadata_path = resolve_output(config, config["dataset_metadata_file"])
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")

    if output_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"Dataset already exists: {output_path}\nUse --overwrite to replace it."
        )

    pairs = pair_partitions(config["prime_root"], config["gap_root"])
    started = time.time()

    if tmp_path.exists():
        tmp_path.unlink()

    out = open_memmap(tmp_path, mode="w+", dtype=np.uint64, shape=(target_count,))
    written = 0
    partition_stats = []

    try:
        for partition_index, (prime_file, gap_file) in enumerate(pairs, start=1):
            primes = np.load(prime_file, mmap_mode="r")
            gaps = np.load(gap_file, mmap_mode="r")

            if len(primes) != len(gaps):
                raise ValueError(
                    f"Length mismatch: {prime_file.name}={len(primes)}, "
                    f"{gap_file.name}={len(gaps)}"
                )

            local_indices = np.flatnonzero(gaps == 2)
            remaining = target_count - written
            if remaining <= 0:
                break

            take = min(remaining, len(local_indices))
            if take:
                selected = np.asarray(primes[local_indices[:take]], dtype=np.uint64)
                out[written : written + take] = selected
                written += take

            partition_stats.append(
                {
                    "partition_index": partition_index,
                    "prime_file": prime_file.name,
                    "gap_file": gap_file.name,
                    "left_twins_found": int(len(local_indices)),
                    "left_twins_written": int(take),
                    "cumulative_written": int(written),
                }
            )

            print(
                f"[{partition_index:03d}/{len(pairs):03d}] "
                f"found={len(local_indices):,} written={written:,}/{target_count:,}"
            )

            if written >= target_count:
                break

        if written != target_count:
            raise RuntimeError(
                f"Insufficient left twin primes: requested={target_count:,}, found={written:,}"
            )

        out.flush()
        del out

        if output_path.exists():
            output_path.unlink()
        os.replace(tmp_path, output_path)

    except Exception:
        try:
            del out
        except Exception:
            pass
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    data = np.load(output_path, mmap_mode="r")
    if np.any(data[1:] <= data[:-1]):
        raise ValueError("Generated left twin prime sequence is not strictly increasing.")

    metadata = {
        "experiment_id": config["experiment_id"],
        "definition": "ltp(i) is the i-th prime q such that q+2 is prime",
        "convention": "include both 3 and 5 because 3+2 and 5+2 are prime",
        "dtype": str(data.dtype),
        "count": int(len(data)),
        "first_value": int(data[0]),
        "last_observed_value": int(data[-2]),
        "held_out_target_value": int(data[-1]),
        "held_out_target_index_1_based": int(len(data)),
        "elapsed_seconds": time.time() - started,
        "sha256": sha256_file(output_path),
        "partition_stats": partition_stats,
    }
    write_json(metadata_path, metadata)

    print()
    print("DATASET GENERATION PASSED")
    print(f"Dataset: {output_path}")
    print(f"Count:   {len(data):,}")
    print(f"First:   {int(data[0]):,}")
    print(f"Last:    {int(data[-1]):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
