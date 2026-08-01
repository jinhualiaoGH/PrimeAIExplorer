"""Load C4 output bundles for report generation."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ReportInputs:
    analysis: Mapping[str, Any]
    leaderboard: tuple[Mapping[str, str], ...]
    comparisons: tuple[Mapping[str, str], ...]
    source_directory: Path


def load_report_inputs(source_directory: str | Path) -> ReportInputs:
    source = Path(source_directory)
    analysis_path = source / "analysis.json"

    if not analysis_path.exists():
        raise FileNotFoundError(analysis_path)

    analysis = json.loads(
        analysis_path.read_text(encoding="utf-8-sig")
    )
    if not isinstance(analysis, dict):
        raise ValueError("analysis.json must contain a JSON object.")

    leaderboard = _read_csv(source / "leaderboard.csv")
    comparisons = _read_csv(source / "comparisons.csv")

    return ReportInputs(
        analysis=analysis,
        leaderboard=tuple(leaderboard),
        comparisons=tuple(comparisons),
        source_directory=source.resolve(),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]
