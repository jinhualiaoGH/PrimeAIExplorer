"""Load PrimeAIExplorer experiment, metrics, dataset, and report artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{source} must contain a JSON object.")
    return value


def load_optional_json_object(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    source = Path(path)
    if not source.exists():
        return None
    return load_json_object(source)


def discover_experiment_files(
    experiment_directory: str | Path,
) -> dict[str, Path | None]:
    root = Path(experiment_directory)
    return {
        "experiment": root / "experiment.json",
        "state": root / "state.json",
        "responses": root / "results" / "responses.jsonl",
    }


def count_jsonl_records(path: str | Path | None) -> int | None:
    if path is None:
        return None
    source = Path(path)
    if not source.exists():
        return None
    with source.open("r", encoding="utf-8-sig") as handle:
        return sum(1 for line in handle if line.strip())
