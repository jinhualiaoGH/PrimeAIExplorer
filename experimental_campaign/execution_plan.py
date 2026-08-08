from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .materialization import ExperimentMaterialization, MaterializedCase
from .validation import require_positive_int, require_text


@dataclass(frozen=True, slots=True)
class ExecutionJob:
    job_id: str
    case_id: str
    case_sha256: str
    experiment_id: str
    target_id: str
    provider: str
    model: str
    repetition_index: int
    seed: int | None
    timeout_seconds: float | None
    retry_budget: int
    lane_id: str
    batch_id: str
    ordinal: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "job_id",
            "case_id",
            "case_sha256",
            "experiment_id",
            "target_id",
            "provider",
            "model",
            "lane_id",
            "batch_id",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        object.__setattr__(
            self,
            "repetition_index",
            require_positive_int("repetition_index", self.repetition_index),
        )
        object.__setattr__(self, "ordinal", require_positive_int("ordinal", self.ordinal))

        if self.seed is not None and (
            isinstance(self.seed, bool) or not isinstance(self.seed, int)
        ):
            raise ValidationError("seed must be an integer or None.")

        if self.timeout_seconds is not None:
            if isinstance(self.timeout_seconds, bool) or not isinstance(
                self.timeout_seconds, (int, float)
            ):
                raise ValidationError("timeout_seconds must be numeric or None.")
            if float(self.timeout_seconds) <= 0:
                raise ValidationError("timeout_seconds must be positive.")
            object.__setattr__(self, "timeout_seconds", float(self.timeout_seconds))

        if (
            isinstance(self.retry_budget, bool)
            or not isinstance(self.retry_budget, int)
            or self.retry_budget < 0
        ):
            raise ValidationError("retry_budget must be a non-negative integer.")

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h4.0",
            "case_id": self.case_id,
            "case_sha256": self.case_sha256,
            "experiment_id": self.experiment_id,
            "target_id": self.target_id,
            "provider": self.provider,
            "model": self.model,
            "repetition_index": self.repetition_index,
            "seed": self.seed,
            "timeout_seconds": self.timeout_seconds,
            "retry_budget": self.retry_budget,
            "lane_id": self.lane_id,
            "batch_id": self.batch_id,
            "ordinal": self.ordinal,
            "metadata": dict(self.metadata),
        }

    @property
    def job_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["job_id"] = self.job_id
        payload["job_sha256"] = self.job_sha256
        return payload


@dataclass(frozen=True, slots=True)
class ExecutionBatch:
    batch_id: str
    ordinal: int
    job_ids: tuple[str, ...]
    provider_targets: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "batch_id", require_text("batch_id", self.batch_id))
        object.__setattr__(self, "ordinal", require_positive_int("ordinal", self.ordinal))

        job_ids = tuple(require_text("job_id", value) for value in self.job_ids)
        if not job_ids:
            raise ValidationError("job_ids cannot be empty.")
        if len(set(job_ids)) != len(job_ids):
            raise ValidationError("job_ids contains duplicate values.")
        object.__setattr__(self, "job_ids", tuple(sorted(job_ids)))

        targets = tuple(require_text("provider_target", value) for value in self.provider_targets)
        if len(set(targets)) != len(targets):
            raise ValidationError("provider_targets contains duplicate values.")
        object.__setattr__(self, "provider_targets", tuple(sorted(targets)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h4.0",
            "batch_id": self.batch_id,
            "ordinal": self.ordinal,
            "job_ids": list(self.job_ids),
            "provider_targets": list(self.provider_targets),
            "metadata": dict(self.metadata),
        }

    @property
    def batch_sha256(self) -> str:
        return sha256_json(self.to_dict())


@dataclass(frozen=True, slots=True)
class CampaignExecutionPlan:
    plan_id: str
    materialization_sha256: str
    jobs: tuple[ExecutionJob, ...]
    batches: tuple[ExecutionBatch, ...]
    lane_ids: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", require_text("plan_id", self.plan_id))
        object.__setattr__(
            self,
            "materialization_sha256",
            require_text("materialization_sha256", self.materialization_sha256),
        )

        jobs = tuple(self.jobs)
        for job in jobs:
            if not isinstance(job, ExecutionJob):
                raise ValidationError("jobs must contain ExecutionJob values.")
        job_ids = tuple(job.job_id for job in jobs)
        if len(set(job_ids)) != len(job_ids):
            raise ValidationError("jobs contains duplicate job IDs.")
        object.__setattr__(self, "jobs", tuple(sorted(jobs, key=lambda job: job.ordinal)))

        batches = tuple(self.batches)
        for batch in batches:
            if not isinstance(batch, ExecutionBatch):
                raise ValidationError("batches must contain ExecutionBatch values.")
        batch_ids = tuple(batch.batch_id for batch in batches)
        if len(set(batch_ids)) != len(batch_ids):
            raise ValidationError("batches contains duplicate batch IDs.")
        object.__setattr__(self, "batches", tuple(sorted(batches, key=lambda batch: batch.ordinal)))

        lanes = tuple(require_text("lane_id", value) for value in self.lane_ids)
        if len(set(lanes)) != len(lanes):
            raise ValidationError("lane_ids contains duplicate values.")
        object.__setattr__(self, "lane_ids", tuple(sorted(lanes)))

        referenced_jobs = {
            job_id
            for batch in self.batches
            for job_id in batch.job_ids
        }
        if referenced_jobs != set(job_ids):
            raise ValidationError("batches must reference every planned job exactly once.")

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def job_count(self) -> int:
        return len(self.jobs)

    @property
    def batch_count(self) -> int:
        return len(self.batches)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h4.0",
            "materialization_sha256": self.materialization_sha256,
            "job_sha256s": [job.job_sha256 for job in self.jobs],
            "batch_sha256s": [batch.batch_sha256 for batch in self.batches],
            "lane_ids": list(self.lane_ids),
            "metadata": dict(self.metadata),
        }

    @property
    def plan_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "plan_id": self.plan_id,
                "plan_sha256": self.plan_sha256,
                "job_count": self.job_count,
                "batch_count": self.batch_count,
                "jobs": [job.to_dict() for job in self.jobs],
                "batches": [batch.to_dict() for batch in self.batches],
            }
        )
        return payload
