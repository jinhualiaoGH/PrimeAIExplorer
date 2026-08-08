from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .contracts import ExecutionPolicy, ExperimentDefinition
from .execution_plan import CampaignExecutionPlan, ExecutionBatch, ExecutionJob
from .identity import canonical_metadata, sha256_json
from .materialization import ExperimentMaterialization, MaterializedCase
from .validation import require_positive_int, require_text


@dataclass(frozen=True, slots=True)
class PlanningPolicy:
    batch_size: int = 32
    max_parallel_jobs: int | None = None
    preserve_provider_affinity: bool = True
    retry_budget_override: int | None = None
    timeout_seconds_override: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "batch_size", require_positive_int("batch_size", self.batch_size))

        if self.max_parallel_jobs is not None:
            object.__setattr__(
                self,
                "max_parallel_jobs",
                require_positive_int("max_parallel_jobs", self.max_parallel_jobs),
            )

        if not isinstance(self.preserve_provider_affinity, bool):
            raise ValidationError("preserve_provider_affinity must be boolean.")

        if self.retry_budget_override is not None:
            if (
                isinstance(self.retry_budget_override, bool)
                or not isinstance(self.retry_budget_override, int)
                or self.retry_budget_override < 0
            ):
                raise ValidationError(
                    "retry_budget_override must be a non-negative integer or None."
                )

        if self.timeout_seconds_override is not None:
            if isinstance(self.timeout_seconds_override, bool) or not isinstance(
                self.timeout_seconds_override, (int, float)
            ):
                raise ValidationError(
                    "timeout_seconds_override must be numeric or None."
                )
            if float(self.timeout_seconds_override) <= 0:
                raise ValidationError("timeout_seconds_override must be positive.")
            object.__setattr__(
                self,
                "timeout_seconds_override",
                float(self.timeout_seconds_override),
            )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_size": self.batch_size,
            "max_parallel_jobs": self.max_parallel_jobs,
            "preserve_provider_affinity": self.preserve_provider_affinity,
            "retry_budget_override": self.retry_budget_override,
            "timeout_seconds_override": self.timeout_seconds_override,
            "metadata": dict(self.metadata),
        }


class CampaignExecutionPlanner:
    def plan(
        self,
        *,
        experiment: ExperimentDefinition,
        materialization: ExperimentMaterialization,
        planning_policy: PlanningPolicy | None = None,
        execution_policy: ExecutionPolicy | None = None,
        plan_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> CampaignExecutionPlan:
        if not isinstance(experiment, ExperimentDefinition):
            raise ValidationError("experiment must be ExperimentDefinition.")
        if not isinstance(materialization, ExperimentMaterialization):
            raise ValidationError(
                "materialization must be ExperimentMaterialization."
            )
        if materialization.experiment_id != experiment.experiment_id:
            raise ValidationError("materialization experiment_id mismatch.")
        if materialization.experiment_sha256 != experiment.experiment_sha256:
            raise ValidationError("materialization experiment_sha256 mismatch.")

        planning_policy = planning_policy or PlanningPolicy()
        if not isinstance(planning_policy, PlanningPolicy):
            raise ValidationError("planning_policy must be PlanningPolicy.")

        execution_policy = execution_policy or ExecutionPolicy()
        if not isinstance(execution_policy, ExecutionPolicy):
            raise ValidationError("execution_policy must be ExecutionPolicy.")

        parallelism = (
            planning_policy.max_parallel_jobs
            if planning_policy.max_parallel_jobs is not None
            else execution_policy.max_parallel_jobs
        )

        lane_ids = tuple(f"LANE-{index:03d}" for index in range(1, parallelism + 1))

        ordered_cases = self._order_cases(
            materialization.cases,
            preserve_provider_affinity=planning_policy.preserve_provider_affinity,
        )

        jobs: list[ExecutionJob] = []
        for ordinal, case in enumerate(ordered_cases, start=1):
            lane_id = lane_ids[(ordinal - 1) % len(lane_ids)]
            batch_ordinal = ((ordinal - 1) // planning_policy.batch_size) + 1
            batch_id = f"BATCH-{batch_ordinal:05d}"
            retry_budget = (
                planning_policy.retry_budget_override
                if planning_policy.retry_budget_override is not None
                else experiment.trial_policy.retries_per_trial
            )
            timeout_seconds = (
                planning_policy.timeout_seconds_override
                if planning_policy.timeout_seconds_override is not None
                else experiment.trial_policy.timeout_seconds
            )
            job_id = self._job_id(
                materialization=materialization,
                case=case,
                ordinal=ordinal,
                lane_id=lane_id,
                batch_id=batch_id,
                retry_budget=retry_budget,
                timeout_seconds=timeout_seconds,
            )

            jobs.append(
                ExecutionJob(
                    job_id=job_id,
                    case_id=case.case_id,
                    case_sha256=case.case_sha256,
                    experiment_id=case.experiment_id,
                    target_id=case.target_id,
                    provider=case.provider,
                    model=case.model,
                    repetition_index=case.repetition_index,
                    seed=case.seed,
                    timeout_seconds=timeout_seconds,
                    retry_budget=retry_budget,
                    lane_id=lane_id,
                    batch_id=batch_id,
                    ordinal=ordinal,
                    metadata={
                        "source_record_id": case.source_record_id,
                        "prompt_id": case.prompt_id,
                        "prompt_version": case.prompt_version,
                    },
                )
            )

        batches: list[ExecutionBatch] = []
        batch_count = ceil(len(jobs) / planning_policy.batch_size) if jobs else 0

        for batch_ordinal in range(1, batch_count + 1):
            batch_id = f"BATCH-{batch_ordinal:05d}"
            batch_jobs = tuple(
                job
                for job in jobs
                if job.batch_id == batch_id
            )
            batches.append(
                ExecutionBatch(
                    batch_id=batch_id,
                    ordinal=batch_ordinal,
                    job_ids=tuple(job.job_id for job in batch_jobs),
                    provider_targets=tuple(
                        sorted({job.target_id for job in batch_jobs})
                    ),
                    metadata={
                        "job_count": len(batch_jobs),
                    },
                )
            )

        resolved_plan_id = (
            require_text("plan_id", plan_id)
            if plan_id is not None
            else self._plan_id(
                experiment=experiment,
                materialization=materialization,
                planning_policy=planning_policy,
                execution_policy=execution_policy,
            )
        )

        return CampaignExecutionPlan(
            plan_id=resolved_plan_id,
            materialization_sha256=materialization.materialization_sha256,
            jobs=tuple(jobs),
            batches=tuple(batches),
            lane_ids=lane_ids,
            metadata={
                "experiment_id": experiment.experiment_id,
                "experiment_sha256": experiment.experiment_sha256,
                "planning_policy": planning_policy.to_dict(),
                "execution_policy": execution_policy.to_dict(),
                **dict(metadata or {}),
            },
        )

    @staticmethod
    def _order_cases(
        cases: tuple[MaterializedCase, ...],
        *,
        preserve_provider_affinity: bool,
    ) -> tuple[MaterializedCase, ...]:
        if preserve_provider_affinity:
            return tuple(
                sorted(
                    cases,
                    key=lambda case: (
                        case.target_id,
                        case.source_record_id,
                        case.repetition_index,
                        case.case_id,
                    ),
                )
            )
        return tuple(sorted(cases, key=lambda case: case.case_id))

    @staticmethod
    def _job_id(
        *,
        materialization: ExperimentMaterialization,
        case: MaterializedCase,
        ordinal: int,
        lane_id: str,
        batch_id: str,
        retry_budget: int,
        timeout_seconds: float | None,
    ) -> str:
        digest = sha256_json(
            {
                "schema_version": "h4.0",
                "materialization_sha256": materialization.materialization_sha256,
                "case_sha256": case.case_sha256,
                "ordinal": ordinal,
                "lane_id": lane_id,
                "batch_id": batch_id,
                "retry_budget": retry_budget,
                "timeout_seconds": timeout_seconds,
            }
        )
        return f"JOB-{digest[:20].upper()}"

    @staticmethod
    def _plan_id(
        *,
        experiment: ExperimentDefinition,
        materialization: ExperimentMaterialization,
        planning_policy: PlanningPolicy,
        execution_policy: ExecutionPolicy,
    ) -> str:
        digest = sha256_json(
            {
                "schema_version": "h4.0",
                "experiment_sha256": experiment.experiment_sha256,
                "materialization_sha256": materialization.materialization_sha256,
                "planning_policy": planning_policy.to_dict(),
                "execution_policy": execution_policy.to_dict(),
            }
        )
        return f"PLAN-{digest[:20].upper()}"
