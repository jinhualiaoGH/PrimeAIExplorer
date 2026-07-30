from __future__ import annotations

import argparse

import numpy as np

from common import load_config, pair_partitions


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate aligned PrimeNet prime/gap partitions.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    pairs = pair_partitions(config["prime_root"], config["gap_root"])

    total_primes = 0
    total_gap_twos = 0

    for index, (prime_file, gap_file) in enumerate(pairs, start=1):
        primes = np.load(prime_file, mmap_mode="r")
        gaps = np.load(gap_file, mmap_mode="r")

        if primes.ndim != 1 or gaps.ndim != 1:
            raise ValueError(f"Expected 1-D arrays: {prime_file.name}, {gap_file.name}")
        if len(primes) != len(gaps):
            raise ValueError(
                f"Length mismatch for partition {index}: "
                f"primes={len(primes)}, gaps={len(gaps)}"
            )
        if not np.issubdtype(primes.dtype, np.integer):
            raise TypeError(f"Prime dtype is not integer: {primes.dtype}")
        if not np.issubdtype(gaps.dtype, np.integer):
            raise TypeError(f"Gap dtype is not integer: {gaps.dtype}")

        twin_count = int(np.count_nonzero(gaps == 2))
        total_primes += len(primes)
        total_gap_twos += twin_count

        print(
            f"[{index:03d}/{len(pairs):03d}] "
            f"{prime_file.name} primes={len(primes):,} left_twins={twin_count:,}"
        )

    print()
    print("SOURCE VALIDATION PASSED")
    print(f"Partitions:       {len(pairs):,}")
    print(f"Stored primes:    {total_primes:,}")
    print(f"Left twin primes: {total_gap_twos:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
