from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from kernel.exceptions import ValidationError
from .checkpoint_contracts import (
    CampaignCheckpoint,
    CheckpointStatus,
    JobCheckpoint,
    ResumeDecision,
)


@dataclass(frozen=True, slots=True)
class ResumePlanner:
    def evaluate(
        self,
        *,
        checkpoint: CampaignCheckpoint,
        expected_campaign_id: str,
        expected_experiment_id: str,
        expected_execution_plan_sha256: str,
        expected_job_ids: Iterable[str],
    ) -> ResumeDecision:
        if not isinstance(checkpoint, CampaignCheckpoint):
            raise ValidationError("checkpoint must be CampaignCheckpoint.")

        expected_job_ids = tuple(sorted(set(expected_job_ids)))

        if checkpoint.campaign_id != expected_campaign_id:
            return ResumeDecision(False, "campaign_id_mismatch", (), expected_job_ids, checkpoint.checkpoint_sha256)
        if checkpoint.experiment_id != expected_experiment_id:
            return ResumeDecision(False, "experiment_id_mismatch", (), expected_job_ids, checkpoint.checkpoint_sha256)
        if checkpoint.execution_plan_sha256 != expected_execution_plan_sha256:
            return ResumeDecision(False, "execution_plan_sha256_mismatch", (), expected_job_ids, checkpoint.checkpoint_sha256)

        checkpoint_ids = tuple(sorted(item.job_id for item in checkpoint.jobs))
        if checkpoint_ids != expected_job_ids:
            return ResumeDecision(False, "job_set_mismatch", (), expected_job_ids, checkpoint.checkpoint_sha256)

        if checkpoint.status == CheckpointStatus.COMPLETED:
            return ResumeDecision(False, "campaign_already_completed", checkpoint_ids, (), checkpoint.checkpoint_sha256)

        completed = tuple(item.job_id for item in checkpoint.jobs if item.completed)
        pending = tuple(item.job_id for item in checkpoint.jobs if not item.completed)
        return ResumeDecision(True, "resume_allowed", completed, pending, checkpoint.checkpoint_sha256)


def next_checkpoint(
    previous: CampaignCheckpoint,
    *,
    status: CheckpointStatus | str,
    jobs: Iterable[JobCheckpoint],
    metadata: dict | None = None,
) -> CampaignCheckpoint:
    if not isinstance(previous, CampaignCheckpoint):
        raise ValidationError("previous must be CampaignCheckpoint.")
    return CampaignCheckpoint(
        checkpoint_id=f"{previous.checkpoint_id}-R{previous.checkpoint_sequence + 1}",
        campaign_id=previous.campaign_id,
        experiment_id=previous.experiment_id,
        execution_plan_sha256=previous.execution_plan_sha256,
        checkpoint_sequence=previous.checkpoint_sequence + 1,
        status=status,
        jobs=tuple(jobs),
        parent_checkpoint_sha256=previous.checkpoint_sha256,
        metadata=dict(metadata or {}),
    )
