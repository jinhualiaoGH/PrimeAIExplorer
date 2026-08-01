"""Models for automatic benchmark-campaign orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OrchestratorConfiguration:
    campaign_id: str
    worker_id: str
    lease_seconds: int = 900
    heartbeat_seconds: int = 30
    max_attempts: int = 3
    max_items: int | None = None
    stop_on_failure: bool = False
    retry_backoff_seconds: float = 0.0
    poll_seconds: float = 0.0

    def __post_init__(self) -> None:
        if not self.campaign_id.startswith("CMP-"):
            raise ValueError("campaign_id must begin with 'CMP-'.")
        if not self.worker_id.strip():
            raise ValueError("worker_id must not be empty.")
        if self.lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive.")
        if self.heartbeat_seconds <= 0:
            raise ValueError("heartbeat_seconds must be positive.")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive.")
        if self.max_items is not None and self.max_items <= 0:
            raise ValueError("max_items must be positive when provided.")
        if self.retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds must be non-negative.")
        if self.poll_seconds < 0:
            raise ValueError("poll_seconds must be non-negative.")


@dataclass(frozen=True, slots=True)
class OrchestratorSummary:
    campaign_id: str
    worker_id: str
    claimed: int
    completed: int
    failed: int
    retried: int
    recovered_stale_leases: int
    stopped_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
