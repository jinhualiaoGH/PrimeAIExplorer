"""Models for the persistent experiment catalog."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class CatalogRecord:
    record_id: str
    experiment_id: str
    dataset_id: str | None
    name: str
    status: str
    provider: str | None
    model: str | None
    sequence_type: str | None
    case_count: int | None
    completed_case_count: int | None
    failed_case_count: int | None
    accuracy: float | None
    mean_absolute_error: float | None
    report_path: str | None
    created_at_utc: str | None
    started_at_utc: str | None
    completed_at_utc: str | None
    snapshot_sha256: str
    snapshot: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.record_id.startswith("XR-"):
            raise ValueError("record_id must begin with 'XR-'.")
        if not self.experiment_id.strip():
            raise ValueError("experiment_id must not be empty.")
        if len(self.snapshot_sha256) != 64:
            raise ValueError("snapshot_sha256 must have 64 hexadecimal characters.")
        int(self.snapshot_sha256, 16)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["snapshot"] = dict(self.snapshot)
        return result


@dataclass(frozen=True, slots=True)
class SearchQuery:
    experiment_id: str | None = None
    dataset_id: str | None = None
    provider: str | None = None
    model: str | None = None
    status: str | None = None
    sequence_type: str | None = None
    min_accuracy: float | None = None
    max_accuracy: float | None = None
    text: str | None = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError("limit must be positive.")
        if self.offset < 0:
            raise ValueError("offset must be non-negative.")
        if self.min_accuracy is not None and not 0.0 <= self.min_accuracy <= 1.0:
            raise ValueError("min_accuracy must be between zero and one.")
        if self.max_accuracy is not None and not 0.0 <= self.max_accuracy <= 1.0:
            raise ValueError("max_accuracy must be between zero and one.")
