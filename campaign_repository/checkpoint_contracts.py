from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from kernel.exceptions import ValidationError
from experimental_campaign.identity import canonical_metadata, sha256_json


def _require_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be a non-empty string.")
    return value.strip()


def _require_non_negative_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{name} must be a non-negative integer.")
    return value


class CheckpointStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class JobCheckpoint:
    job_id: str
    completed: bool
    attempts_completed: int
    result_sha256: str | None = None
    last_error_class: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "job_id", _require_text("job_id", self.job_id))
        object.__setattr__(
            self,
            "attempts_completed",
            _require_non_negative_int("attempts_completed", self.attempts_completed),
        )
        if not isinstance(self.completed, bool):
            raise ValidationError("completed must be bool.")
        if self.result_sha256 is not None:
            object.__setattr__(self, "result_sha256", _require_text("result_sha256", self.result_sha256))
        if self.last_error_class is not None:
            object.__setattr__(self, "last_error_class", _require_text("last_error_class", self.last_error_class))
        if self.completed and self.result_sha256 is None:
            raise ValidationError("completed job checkpoints require result_sha256.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "completed": self.completed,
            "attempts_completed": self.attempts_completed,
            "result_sha256": self.result_sha256,
            "last_error_class": self.last_error_class,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CampaignCheckpoint:
    checkpoint_id: str
    campaign_id: str
    experiment_id: str
    execution_plan_sha256: str
    checkpoint_sequence: int
    status: CheckpointStatus
    jobs: tuple[JobCheckpoint, ...]
    parent_checkpoint_sha256: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("checkpoint_id", "campaign_id", "experiment_id", "execution_plan_sha256"):
            object.__setattr__(self, name, _require_text(name, getattr(self, name)))
        object.__setattr__(
            self,
            "checkpoint_sequence",
            _require_non_negative_int("checkpoint_sequence", self.checkpoint_sequence),
        )
        if not isinstance(self.status, CheckpointStatus):
            try:
                object.__setattr__(self, "status", CheckpointStatus(self.status))
            except Exception as exc:
                raise ValidationError("invalid checkpoint status.") from exc
        jobs = tuple(self.jobs)
        if any(not isinstance(item, JobCheckpoint) for item in jobs):
            raise ValidationError("jobs must contain JobCheckpoint values.")
        ids = [item.job_id for item in jobs]
        if len(ids) != len(set(ids)):
            raise ValidationError("checkpoint contains duplicate job IDs.")
        object.__setattr__(self, "jobs", tuple(sorted(jobs, key=lambda item: item.job_id)))
        if self.parent_checkpoint_sha256 is not None:
            object.__setattr__(
                self,
                "parent_checkpoint_sha256",
                _require_text("parent_checkpoint_sha256", self.parent_checkpoint_sha256),
            )
        if self.checkpoint_sequence == 0 and self.parent_checkpoint_sha256 is not None:
            raise ValidationError("sequence-0 checkpoint cannot have a parent.")
        if self.checkpoint_sequence > 0 and self.parent_checkpoint_sha256 is None:
            raise ValidationError("checkpoint sequence > 0 requires parent_checkpoint_sha256.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def total_jobs(self) -> int:
        return len(self.jobs)

    @property
    def completed_jobs(self) -> int:
        return sum(item.completed for item in self.jobs)

    @property
    def pending_jobs(self) -> int:
        return self.total_jobs - self.completed_jobs

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "i3.0",
            "campaign_id": self.campaign_id,
            "experiment_id": self.experiment_id,
            "execution_plan_sha256": self.execution_plan_sha256,
            "checkpoint_sequence": self.checkpoint_sequence,
            "status": self.status.value,
            "jobs": [item.to_dict() for item in self.jobs],
            "parent_checkpoint_sha256": self.parent_checkpoint_sha256,
            "metadata": dict(self.metadata),
        }

    @property
    def checkpoint_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update({
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "total_jobs": self.total_jobs,
            "completed_jobs": self.completed_jobs,
            "pending_jobs": self.pending_jobs,
        })
        return payload


@dataclass(frozen=True, slots=True)
class ResumeDecision:
    resumable: bool
    reason: str
    completed_job_ids: tuple[str, ...]
    pending_job_ids: tuple[str, ...]
    checkpoint_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.resumable, bool):
            raise ValidationError("resumable must be bool.")
        object.__setattr__(self, "reason", _require_text("reason", self.reason))
        completed = tuple(_require_text("completed_job_id", item) for item in self.completed_job_ids)
        pending = tuple(_require_text("pending_job_id", item) for item in self.pending_job_ids)
        if set(completed) & set(pending):
            raise ValidationError("completed and pending job IDs must be disjoint.")
        object.__setattr__(self, "completed_job_ids", tuple(sorted(completed)))
        object.__setattr__(self, "pending_job_ids", tuple(sorted(pending)))
        if self.checkpoint_sha256 is not None:
            object.__setattr__(
                self,
                "checkpoint_sha256",
                _require_text("checkpoint_sha256", self.checkpoint_sha256),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "resumable": self.resumable,
            "reason": self.reason,
            "completed_job_ids": list(self.completed_job_ids),
            "pending_job_ids": list(self.pending_job_ids),
            "checkpoint_sha256": self.checkpoint_sha256,
        }
