from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable


_RANGE_RE = re.compile(r"(\d+)_(\d+)")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def range_key(path: Path) -> tuple[int, int, str]:
    match = _RANGE_RE.search(path.stem)
    if match:
        return int(match.group(1)), int(match.group(2)), path.name.lower()
    return 10**30, 10**30, path.name.lower()


def sorted_npy_files(root: str | Path) -> list[Path]:
    files = sorted(Path(root).glob("*.npy"), key=range_key)
    if not files:
        raise FileNotFoundError(f"No .npy files found under {root}")
    return files


def pair_partitions(prime_root: str | Path, gap_root: str | Path) -> list[tuple[Path, Path]]:
    primes = sorted_npy_files(prime_root)
    gaps = sorted_npy_files(gap_root)
    if len(primes) != len(gaps):
        raise ValueError(f"Partition count mismatch: primes={len(primes)}, gaps={len(gaps)}")

    pairs = []
    for prime_file, gap_file in zip(primes, gaps, strict=True):
        if range_key(prime_file)[:2] != range_key(gap_file)[:2]:
            raise ValueError(
                f"Range mismatch: {prime_file.name} versus {gap_file.name}"
            )
        pairs.append((prime_file, gap_file))
    return pairs
