from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from typing import Any, Callable, Mapping, Protocol

from kernel.exceptions import ValidationError

from .execution_plan import CampaignExecutionPlan, ExecutionJob
from .identity import canonical_metadata, sha256_json
from .validation import require_positive_int, require_text


class JobExecutionStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXHAUSTED = "exhausted"


@dataclass(frozen=True, slots=True)
class AttemptOutcome:
    successful: bool
    response_text: str | None = None
    error_class: str | None = None
    error_message: str | None = None
    retryable: bool = False
    provider_request_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.successful, bool):
            raise ValidationError("successful must be boolean.")
        if not isinstance(self.retryable, bool):
            raise ValidationError("retryable must be boolean.")
        if self.response_text is not None and not isinstance(self.response_text, str):
            raise ValidationError("response_text must be a string or None.")

        for name in ("error_class", "error_message", "provider_request_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_text(name, value))

        if self.successful and (self.error_class is not None or self.error_message is not None):
            raise ValidationError(
                "successful AttemptOutcome cannot contain error information."
            )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def scientific_payload(self) -> dict[str, Any]:
        return {
            "successful": self.successful,
            "response_text": self.response_text,
            "error_class": self.error_class,
            "error_message": self.error_message,
            "retryable": self.retryable,
            "provider_request_id": self.provider_request_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ExecutionAttempt:
    attempt_index: int
    outcome: AttemptOutcome
    duration_seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "attempt_index",
            require_positive_int("attempt_index", self.attempt_index),
        )
        if not isinstance(self.outcome, AttemptOutcome):
            raise ValidationError("outcome must be AttemptOutcome.")
        if isinstance(self.duration_seconds, bool) or not isinstance(
            self.duration_seconds, (int, float)
        ):
            raise ValidationError("duration_seconds must be numeric.")
        if float(self.duration_seconds) < 0:
            raise ValidationError("duration_seconds cannot be negative.")
        object.__setattr__(self, "duration_seconds", float(self.duration_seconds))

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_index": self.attempt_index,
            "outcome": self.outcome.scientific_payload(),
            "duration_seconds": self.duration_seconds,
        }


@dataclass(frozen=True, slots=True)
class JobExecutionRecord:
    job_id: str
    job_sha256: str
    case_id: str
    case_sha256: str
    status: JobExecutionStatus
    attempts: tuple[ExecutionAttempt, ...]
    terminal_outcome: AttemptOutcome
    total_duration_seconds: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("job_id", "job_sha256", "case_id", "case_sha256"):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if not isinstance(self.status, JobExecutionStatus):
            try:
                object.__setattr__(self, "status", JobExecutionStatus(self.status))
            except Exception as exc:
                raise ValidationError("invalid job execution status.") from exc

        attempts = tuple(self.attempts)
        if not attempts:
            raise ValidationError("attempts cannot be empty.")
        if any(not isinstance(item, ExecutionAttempt) for item in attempts):
            raise ValidationError("attempts must contain ExecutionAttempt values.")
        expected = tuple(range(1, len(attempts) + 1))
        actual = tuple(item.attempt_index for item in attempts)
        if actual != expected:
            raise ValidationError("attempt indices must be contiguous starting at 1.")
        object.__setattr__(self, "attempts", attempts)

        if not isinstance(self.terminal_outcome, AttemptOutcome):
            raise ValidationError("terminal_outcome must be AttemptOutcome.")
        if self.terminal_outcome != attempts[-1].outcome:
            raise ValidationError("terminal_outcome must match the final attempt outcome.")

        if self.status == JobExecutionStatus.SUCCEEDED and not self.terminal_outcome.successful:
            raise ValidationError("succeeded record requires successful terminal outcome.")
        if self.status != JobExecutionStatus.SUCCEEDED and self.terminal_outcome.successful:
            raise ValidationError("failed/exhausted record cannot have successful terminal outcome.")

        if isinstance(self.total_duration_seconds, bool) or not isinstance(
            self.total_duration_seconds, (int, float)
        ):
            raise ValidationError("total_duration_seconds must be numeric.")
        if float(self.total_duration_seconds) < 0:
            raise ValidationError("total_duration_seconds cannot be negative.")
        object.__setattr__(
            self,
            "total_duration_seconds",
            float(self.total_duration_seconds),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)

    def scientific_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h5.0",
            "job_id": self.job_id,
            "job_sha256": self.job_sha256,
            "case_id": self.case_id,
            "case_sha256": self.case_sha256,
            "status": self.status.value,
            "attempts": [
                {
                    "attempt_index": item.attempt_index,
                    "outcome": item.outcome.scientific_payload(),
                }
                for item in self.attempts
            ],
            "metadata": dict(self.metadata),
        }

    @property
    def record_sha256(self) -> str:
        return sha256_json(self.scientific_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.scientific_payload()
        payload.update(
            {
                "record_sha256": self.record_sha256,
                "attempt_count": self.attempt_count,
                "total_duration_seconds": self.total_duration_seconds,
                "attempts": [item.to_dict() for item in self.attempts],
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class CampaignExecutionRun:
    run_id: str
    plan_id: str
    plan_sha256: str
    records: tuple[JobExecutionRecord, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("run_id", "plan_id", "plan_sha256"):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        records = tuple(self.records)
        if any(not isinstance(item, JobExecutionRecord) for item in records):
            raise ValidationError("records must contain JobExecutionRecord values.")
        job_ids = tuple(record.job_id for record in records)
        if len(set(job_ids)) != len(job_ids):
            raise ValidationError("records contains duplicate job IDs.")
        object.__setattr__(self, "records", tuple(sorted(records, key=lambda item: item.job_id)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def job_count(self) -> int:
        return len(self.records)

    @property
    def succeeded_count(self) -> int:
        return sum(record.status == JobExecutionStatus.SUCCEEDED for record in self.records)

    @property
    def failed_count(self) -> int:
        return sum(record.status == JobExecutionStatus.FAILED for record in self.records)

    @property
    def exhausted_count(self) -> int:
        return sum(record.status == JobExecutionStatus.EXHAUSTED for record in self.records)

    @property
    def total_attempts(self) -> int:
        return sum(record.attempt_count for record in self.records)

    def scientific_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h5.0",
            "plan_id": self.plan_id,
            "plan_sha256": self.plan_sha256,
            "record_sha256s": [record.record_sha256 for record in self.records],
            "metadata": dict(self.metadata),
        }

    @property
    def run_sha256(self) -> str:
        return sha256_json(self.scientific_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.scientific_payload()
        payload.update(
            {
                "run_id": self.run_id,
                "run_sha256": self.run_sha256,
                "job_count": self.job_count,
                "succeeded_count": self.succeeded_count,
                "failed_count": self.failed_count,
                "exhausted_count": self.exhausted_count,
                "total_attempts": self.total_attempts,
                "records": [record.to_dict() for record in self.records],
            }
        )
        return payload


class JobExecutor(Protocol):
    def __call__(self, job: ExecutionJob, attempt_index: int) -> AttemptOutcome:
        ...


class CampaignExecutionRuntime:
    def execute(
        self,
        *,
        plan: CampaignExecutionPlan,
        executor: JobExecutor | Callable[[ExecutionJob, int], AttemptOutcome],
        run_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> CampaignExecutionRun:
        if not isinstance(plan, CampaignExecutionPlan):
            raise ValidationError("plan must be CampaignExecutionPlan.")
        if not callable(executor):
            raise ValidationError("executor must be callable.")

        resolved_run_id = (
            require_text("run_id", run_id)
            if run_id is not None
            else f"RUN-{plan.plan_sha256[:20].upper()}"
        )

        records = tuple(
            self._execute_job(job=job, executor=executor)
            for job in plan.jobs
        )

        return CampaignExecutionRun(
            run_id=resolved_run_id,
            plan_id=plan.plan_id,
            plan_sha256=plan.plan_sha256,
            records=records,
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _execute_job(
        *,
        job: ExecutionJob,
        executor: JobExecutor | Callable[[ExecutionJob, int], AttemptOutcome],
    ) -> JobExecutionRecord:
        attempts: list[ExecutionAttempt] = []
        maximum_attempts = 1 + job.retry_budget

        for attempt_index in range(1, maximum_attempts + 1):
            started = perf_counter()
            try:
                outcome = executor(job, attempt_index)
            except Exception as exc:
                outcome = AttemptOutcome(
                    successful=False,
                    error_class=exc.__class__.__name__,
                    error_message=str(exc) or exc.__class__.__name__,
                    retryable=False,
                )
            elapsed = perf_counter() - started

            if not isinstance(outcome, AttemptOutcome):
                raise ValidationError("executor must return AttemptOutcome.")

            attempts.append(
                ExecutionAttempt(
                    attempt_index=attempt_index,
                    outcome=outcome,
                    duration_seconds=elapsed,
                )
            )

            if outcome.successful:
                status = JobExecutionStatus.SUCCEEDED
                break

            if not outcome.retryable:
                status = JobExecutionStatus.FAILED
                break
        else:
            status = JobExecutionStatus.EXHAUSTED

        terminal = attempts[-1].outcome
        total_duration = sum(item.duration_seconds for item in attempts)

        return JobExecutionRecord(
            job_id=job.job_id,
            job_sha256=job.job_sha256,
            case_id=job.case_id,
            case_sha256=job.case_sha256,
            status=status,
            attempts=tuple(attempts),
            terminal_outcome=terminal,
            total_duration_seconds=total_duration,
            metadata={
                "target_id": job.target_id,
                "provider": job.provider,
                "model": job.model,
                "lane_id": job.lane_id,
                "batch_id": job.batch_id,
                "ordinal": job.ordinal,
            },
        )
