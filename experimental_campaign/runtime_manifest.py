from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .runtime import CampaignExecutionRun
from .validation import require_text


@dataclass(frozen=True, slots=True)
class CampaignRunManifest:
    run_id: str
    run_sha256: str
    plan_id: str
    plan_sha256: str
    job_count: int
    succeeded_count: int
    failed_count: int
    exhausted_count: int
    total_attempts: int
    record_sha256s: tuple[str, ...]
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("run_id", "run_sha256", "plan_id", "plan_sha256", "source"):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        for name in (
            "job_count",
            "succeeded_count",
            "failed_count",
            "exhausted_count",
            "total_attempts",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValidationError(f"{name} must be a non-negative integer.")

        if self.succeeded_count + self.failed_count + self.exhausted_count != self.job_count:
            raise ValidationError("terminal status counts must equal job_count.")

        digests = tuple(require_text("record_sha256", value) for value in self.record_sha256s)
        if len(digests) != self.job_count:
            raise ValidationError("record_sha256s count must equal job_count.")
        if len(set(digests)) != len(digests) and self.job_count > 1:
            raise ValidationError("record_sha256s contains duplicate record identities.")
        object.__setattr__(self, "record_sha256s", tuple(sorted(digests)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @classmethod
    def from_run(
        cls,
        run: CampaignExecutionRun,
        *,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CampaignRunManifest":
        if not isinstance(run, CampaignExecutionRun):
            raise ValidationError("run must be CampaignExecutionRun.")

        return cls(
            run_id=run.run_id,
            run_sha256=run.run_sha256,
            plan_id=run.plan_id,
            plan_sha256=run.plan_sha256,
            job_count=run.job_count,
            succeeded_count=run.succeeded_count,
            failed_count=run.failed_count,
            exhausted_count=run.exhausted_count,
            total_attempts=run.total_attempts,
            record_sha256s=tuple(record.record_sha256 for record in run.records),
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h5.0",
            "run_id": self.run_id,
            "run_sha256": self.run_sha256,
            "plan_id": self.plan_id,
            "plan_sha256": self.plan_sha256,
            "job_count": self.job_count,
            "succeeded_count": self.succeeded_count,
            "failed_count": self.failed_count,
            "exhausted_count": self.exhausted_count,
            "total_attempts": self.total_attempts,
            "record_sha256s": list(self.record_sha256s),
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())
