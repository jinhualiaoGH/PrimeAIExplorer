from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

import numpy as np


_RANGE_RE = re.compile(r"(\d+)_(\d+)")


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    config["_config_path"] = str(config_path)
    return config


def experiment_root(config: dict[str, Any]) -> Path:
    return Path(config["output_root"]).resolve()


def resolve_output(config: dict[str, Any], relative_path: str) -> Path:
    return experiment_root(config) / relative_path


def numeric_range_key(path: Path) -> tuple[int, int, str]:
    match = _RANGE_RE.search(path.stem)
    if not match:
        return (10**30, 10**30, path.name.lower())
    return (int(match.group(1)), int(match.group(2)), path.name.lower())


def sorted_npy_files(root: str | Path) -> list[Path]:
    base = Path(root)
    files = sorted(base.glob("*.npy"), key=numeric_range_key)
    if not files:
        raise FileNotFoundError(f"No .npy files found under: {base}")
    return files


def pair_partitions(prime_root: str | Path, gap_root: str | Path) -> list[tuple[Path, Path]]:
    prime_files = sorted_npy_files(prime_root)
    gap_files = sorted_npy_files(gap_root)

    if len(prime_files) != len(gap_files):
        raise ValueError(
            f"Partition count mismatch: primes={len(prime_files)}, gaps={len(gap_files)}"
        )

    pairs: list[tuple[Path, Path]] = []
    for prime_file, gap_file in zip(prime_files, gap_files, strict=True):
        p_key = numeric_range_key(prime_file)[:2]
        g_key = numeric_range_key(gap_file)[:2]
        if p_key != g_key:
            raise ValueError(
                "Partition range mismatch:\n"
                f"  prime: {prime_file.name} -> {p_key}\n"
                f"  gap:   {gap_file.name} -> {g_key}"
            )
        pairs.append((prime_file, gap_file))
    return pairs


def load_ltp_dataset(config: dict[str, Any], mmap_mode: str = "r") -> np.ndarray:
    path = resolve_output(config, config["dataset_file"])
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    data = np.load(path, mmap_mode=mmap_mode)
    if data.dtype != np.uint64:
        raise TypeError(f"Expected uint64 dataset, found {data.dtype}")
    return data


def ensure_directories(config: dict[str, Any]) -> None:
    root = experiment_root(config)
    for name in ("data", "cases", "prompts", "responses", "results", "reports"):
        (root / name).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


def iter_json_files(root: Path, pattern: str) -> Iterable[Path]:
    yield from sorted(root.glob(pattern))
