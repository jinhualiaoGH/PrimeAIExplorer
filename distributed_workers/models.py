"""Data models for Phase D5 distributed campaign execution."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class DistributedConfiguration:
    campaign_id: str
    worker_prefix: str = "worker"
    worker_count: int = 2
    lease_seconds: int = 900
    heartbeat_seconds: float = 5.0
    stale_after_seconds: float = 30.0
    max_attempts: int = 3
    max_items_per_worker: int | None = None
    retry_backoff_seconds: float = 0.0

    def __post_init__(self) -> None:
        if not self.campaign_id.startswith("CMP-"):
            raise ValueError("campaign_id must begin with 'CMP-'.")
        if not self.worker_prefix.strip():
            raise ValueError("worker_prefix must not be empty.")
        if self.worker_count <= 0:
            raise ValueError("worker_count must be positive.")
        if self.lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive.")
        if self.heartbeat_seconds <= 0:
            raise ValueError("heartbeat_seconds must be positive.")
        if self.stale_after_seconds <= 0:
            raise ValueError("stale_after_seconds must be positive.")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive.")
        if self.max_items_per_worker is not None and self.max_items_per_worker <= 0:
            raise ValueError("max_items_per_worker must be positive.")

@dataclass(frozen=True, slots=True)
class DistributedSummary:
    campaign_id: str
    worker_count: int
    claimed: int
    completed: int
    failed: int
    retried: int
    recovered_stale_workers: int
    stopped_workers: int
    elapsed_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
