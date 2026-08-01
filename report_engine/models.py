"""Models for scientific reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReportSummary:
    title: str
    experiment_label: str
    record_count: int
    evaluable_count: int
    accuracy: float | None
    mean_absolute_error: float | None
    root_mean_squared_error: float | None
    expected_calibration_error: float | None
    mean_latency_seconds: float | None
    bootstrap_accuracy_lower: float | None
    bootstrap_accuracy_upper: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReportManifest:
    schema_version: str
    title: str
    experiment_label: str
    generated_files: tuple[str, ...]
    source_files: tuple[str, ...]
    deterministic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
