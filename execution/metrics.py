from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from execution.models import ExecutionRecord
from kernel.serialization import stable_sha256


@dataclass
class ExecutionMetrics:
    submitted_count: int = 0
    completed_count: int = 0
    succeeded_count: int = 0
    failed_count: int = 0
    total_elapsed_seconds: float = 0.0

    def record_submission(self) -> None:
        self.submitted_count += 1

    def record_completion(self, record: ExecutionRecord) -> None:
        self.completed_count += 1
        self.total_elapsed_seconds += record.elapsed_seconds
        if record.success:
            self.succeeded_count += 1
        else:
            self.failed_count += 1

    @property
    def mean_elapsed_seconds(self) -> float:
        if self.completed_count == 0:
            return 0.0
        return self.total_elapsed_seconds / self.completed_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "submitted_count": self.submitted_count,
            "completed_count": self.completed_count,
            "succeeded_count": self.succeeded_count,
            "failed_count": self.failed_count,
            "total_elapsed_seconds": self.total_elapsed_seconds,
            "mean_elapsed_seconds": self.mean_elapsed_seconds,
        }

    @property
    def metrics_sha256(self) -> str:
        return stable_sha256(self.to_dict())
