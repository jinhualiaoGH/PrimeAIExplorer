from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .execution_plan import CampaignExecutionPlan
from .identity import canonical_metadata, sha256_json
from .validation import require_text


@dataclass(frozen=True, slots=True)
class ExecutionPlanManifest:
    plan_id: str
    plan_sha256: str
    materialization_sha256: str
    job_count: int
    batch_count: int
    job_ids: tuple[str, ...]
    batch_ids: tuple[str, ...]
    lane_ids: tuple[str, ...]
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "plan_id",
            "plan_sha256",
            "materialization_sha256",
            "source",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        for name in ("job_count", "batch_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValidationError(f"{name} must be a non-negative integer.")

        job_ids = tuple(require_text("job_id", value) for value in self.job_ids)
        batch_ids = tuple(require_text("batch_id", value) for value in self.batch_ids)
        lane_ids = tuple(require_text("lane_id", value) for value in self.lane_ids)

        if len(job_ids) != self.job_count:
            raise ValidationError("job_count does not match job_ids.")
        if len(batch_ids) != self.batch_count:
            raise ValidationError("batch_count does not match batch_ids.")
        if len(set(job_ids)) != len(job_ids):
            raise ValidationError("job_ids contains duplicates.")
        if len(set(batch_ids)) != len(batch_ids):
            raise ValidationError("batch_ids contains duplicates.")
        if len(set(lane_ids)) != len(lane_ids):
            raise ValidationError("lane_ids contains duplicates.")

        object.__setattr__(self, "job_ids", tuple(sorted(job_ids)))
        object.__setattr__(self, "batch_ids", tuple(sorted(batch_ids)))
        object.__setattr__(self, "lane_ids", tuple(sorted(lane_ids)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @classmethod
    def from_plan(
        cls,
        plan: CampaignExecutionPlan,
        *,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ExecutionPlanManifest":
        if not isinstance(plan, CampaignExecutionPlan):
            raise ValidationError("plan must be CampaignExecutionPlan.")

        return cls(
            plan_id=plan.plan_id,
            plan_sha256=plan.plan_sha256,
            materialization_sha256=plan.materialization_sha256,
            job_count=plan.job_count,
            batch_count=plan.batch_count,
            job_ids=tuple(job.job_id for job in plan.jobs),
            batch_ids=tuple(batch.batch_id for batch in plan.batches),
            lane_ids=plan.lane_ids,
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h4.0",
            "plan_id": self.plan_id,
            "plan_sha256": self.plan_sha256,
            "materialization_sha256": self.materialization_sha256,
            "job_count": self.job_count,
            "batch_count": self.batch_count,
            "job_ids": list(self.job_ids),
            "batch_ids": list(self.batch_ids),
            "lane_ids": list(self.lane_ids),
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())
