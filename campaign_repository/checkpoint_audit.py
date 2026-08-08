from __future__ import annotations

from dataclasses import dataclass
from kernel.exceptions import ValidationError
from .checkpoint_contracts import CampaignCheckpoint


@dataclass(frozen=True, slots=True)
class CheckpointLineageAudit:
    valid: bool
    checked_count: int
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.valid, bool):
            raise ValidationError("valid must be bool.")
        if isinstance(self.checked_count, bool) or not isinstance(self.checked_count, int) or self.checked_count < 0:
            raise ValidationError("checked_count must be a non-negative integer.")
        object.__setattr__(self, "errors", tuple(str(item) for item in self.errors))

    def to_dict(self) -> dict:
        return {
            "schema_version": "i3.0",
            "valid": self.valid,
            "checked_count": self.checked_count,
            "errors": list(self.errors),
        }


def audit_checkpoint_lineage(checkpoints) -> CheckpointLineageAudit:
    checkpoints = tuple(checkpoints)
    if any(not isinstance(item, CampaignCheckpoint) for item in checkpoints):
        raise ValidationError("checkpoints must contain CampaignCheckpoint values.")
    if not checkpoints:
        return CheckpointLineageAudit(True, 0, ())

    ordered = tuple(sorted(checkpoints, key=lambda item: item.checkpoint_sequence))
    errors = []
    first = ordered[0]

    if first.checkpoint_sequence != 0:
        errors.append("lineage_must_start_at_sequence_0")
    if first.parent_checkpoint_sha256 is not None:
        errors.append("sequence_0_must_not_have_parent")

    campaign = first.campaign_id
    experiment = first.experiment_id
    plan_sha = first.execution_plan_sha256
    job_ids = tuple(item.job_id for item in first.jobs)

    for index, current in enumerate(ordered):
        if current.campaign_id != campaign:
            errors.append(f"campaign_id_mismatch_at_{current.checkpoint_sequence}")
        if current.experiment_id != experiment:
            errors.append(f"experiment_id_mismatch_at_{current.checkpoint_sequence}")
        if current.execution_plan_sha256 != plan_sha:
            errors.append(f"plan_sha256_mismatch_at_{current.checkpoint_sequence}")
        if tuple(item.job_id for item in current.jobs) != job_ids:
            errors.append(f"job_set_mismatch_at_{current.checkpoint_sequence}")

        if index == 0:
            continue

        previous = ordered[index - 1]
        if current.checkpoint_sequence != previous.checkpoint_sequence + 1:
            errors.append(f"non_contiguous_sequence_at_{current.checkpoint_sequence}")
        if current.parent_checkpoint_sha256 != previous.checkpoint_sha256:
            errors.append(f"parent_sha256_mismatch_at_{current.checkpoint_sequence}")

        previous_completed = {item.job_id: item for item in previous.jobs if item.completed}
        current_jobs = {item.job_id: item for item in current.jobs}
        for job_id, previous_job in previous_completed.items():
            if job_id not in current_jobs:
                continue
            current_job = current_jobs[job_id]
            if not current_job.completed:
                errors.append(f"completed_job_regressed:{job_id}:seq{current.checkpoint_sequence}")
            elif current_job.result_sha256 != previous_job.result_sha256:
                errors.append(f"completed_job_result_changed:{job_id}:seq{current.checkpoint_sequence}")

    return CheckpointLineageAudit(len(errors) == 0, len(ordered), tuple(errors))
