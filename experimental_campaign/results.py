from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .runtime import JobExecutionRecord, JobExecutionStatus
from .validation import require_positive_int, require_text


@dataclass(frozen=True, slots=True)
class CampaignResultRecord:
    result_id: str
    job_id: str
    job_sha256: str
    case_id: str
    case_sha256: str
    status: JobExecutionStatus
    attempt_count: int
    response_text: str | None
    provider_request_id: str | None
    error_class: str | None
    error_message: str | None
    provider: str
    model: str
    target_id: str
    lane_id: str
    batch_id: str
    ordinal: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "result_id",
            "job_id",
            "job_sha256",
            "case_id",
            "case_sha256",
            "provider",
            "model",
            "target_id",
            "lane_id",
            "batch_id",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if not isinstance(self.status, JobExecutionStatus):
            try:
                object.__setattr__(self, "status", JobExecutionStatus(self.status))
            except Exception as exc:
                raise ValidationError("invalid result status.") from exc

        object.__setattr__(
            self,
            "attempt_count",
            require_positive_int("attempt_count", self.attempt_count),
        )
        object.__setattr__(self, "ordinal", require_positive_int("ordinal", self.ordinal))

        for name in (
            "response_text",
            "provider_request_id",
            "error_class",
            "error_message",
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                raise ValidationError(f"{name} must be a string or None.")

        if self.status == JobExecutionStatus.SUCCEEDED and self.response_text is None:
            raise ValidationError("successful result requires response_text.")

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h6.0",
            "job_id": self.job_id,
            "job_sha256": self.job_sha256,
            "case_id": self.case_id,
            "case_sha256": self.case_sha256,
            "status": self.status.value,
            "attempt_count": self.attempt_count,
            "response_text": self.response_text,
            "provider_request_id": self.provider_request_id,
            "error_class": self.error_class,
            "error_message": self.error_message,
            "provider": self.provider,
            "model": self.model,
            "target_id": self.target_id,
            "lane_id": self.lane_id,
            "batch_id": self.batch_id,
            "ordinal": self.ordinal,
            "metadata": dict(self.metadata),
        }

    @property
    def result_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["result_id"] = self.result_id
        payload["result_sha256"] = self.result_sha256
        return payload

    @classmethod
    def from_execution_record(
        cls,
        record: JobExecutionRecord,
    ) -> "CampaignResultRecord":
        if not isinstance(record, JobExecutionRecord):
            raise ValidationError("record must be JobExecutionRecord.")

        terminal = record.terminal_outcome
        metadata = dict(record.metadata)

        required = ("provider", "model", "target_id", "lane_id", "batch_id", "ordinal")
        missing = [name for name in required if name not in metadata]
        if missing:
            raise ValidationError(
                "execution record missing planning metadata: " + ", ".join(sorted(missing))
            )

        ordinal = metadata["ordinal"]
        if isinstance(ordinal, bool) or not isinstance(ordinal, int):
            raise ValidationError("execution record ordinal must be an integer.")

        digest = sha256_json(
            {
                "schema_version": "h6.0",
                "job_sha256": record.job_sha256,
                "record_sha256": record.record_sha256,
            }
        )

        return cls(
            result_id=f"RESULT-{digest[:20].upper()}",
            job_id=record.job_id,
            job_sha256=record.job_sha256,
            case_id=record.case_id,
            case_sha256=record.case_sha256,
            status=record.status,
            attempt_count=record.attempt_count,
            response_text=terminal.response_text,
            provider_request_id=terminal.provider_request_id,
            error_class=terminal.error_class,
            error_message=terminal.error_message,
            provider=str(metadata["provider"]),
            model=str(metadata["model"]),
            target_id=str(metadata["target_id"]),
            lane_id=str(metadata["lane_id"]),
            batch_id=str(metadata["batch_id"]),
            ordinal=ordinal,
            metadata={
                "execution_record_sha256": record.record_sha256,
            },
        )


@dataclass(frozen=True, slots=True)
class CampaignResultSet:
    result_set_id: str
    experiment_id: str
    experiment_sha256: str
    materialization_sha256: str
    plan_id: str
    plan_sha256: str
    run_id: str
    run_sha256: str
    results: tuple[CampaignResultRecord, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "result_set_id",
            "experiment_id",
            "experiment_sha256",
            "materialization_sha256",
            "plan_id",
            "plan_sha256",
            "run_id",
            "run_sha256",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        results = tuple(self.results)
        if any(not isinstance(item, CampaignResultRecord) for item in results):
            raise ValidationError("results must contain CampaignResultRecord values.")

        result_ids = tuple(item.result_id for item in results)
        job_ids = tuple(item.job_id for item in results)
        if len(set(result_ids)) != len(result_ids):
            raise ValidationError("results contains duplicate result IDs.")
        if len(set(job_ids)) != len(job_ids):
            raise ValidationError("results contains duplicate job IDs.")

        object.__setattr__(
            self,
            "results",
            tuple(sorted(results, key=lambda item: (item.ordinal, item.job_id))),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def result_count(self) -> int:
        return len(self.results)

    @property
    def succeeded_count(self) -> int:
        return sum(item.status == JobExecutionStatus.SUCCEEDED for item in self.results)

    @property
    def failed_count(self) -> int:
        return sum(item.status == JobExecutionStatus.FAILED for item in self.results)

    @property
    def exhausted_count(self) -> int:
        return sum(item.status == JobExecutionStatus.EXHAUSTED for item in self.results)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h6.0",
            "experiment_id": self.experiment_id,
            "experiment_sha256": self.experiment_sha256,
            "materialization_sha256": self.materialization_sha256,
            "plan_id": self.plan_id,
            "plan_sha256": self.plan_sha256,
            "run_id": self.run_id,
            "run_sha256": self.run_sha256,
            "result_sha256s": [item.result_sha256 for item in self.results],
            "metadata": dict(self.metadata),
        }

    @property
    def result_set_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "result_set_id": self.result_set_id,
                "result_set_sha256": self.result_set_sha256,
                "result_count": self.result_count,
                "succeeded_count": self.succeeded_count,
                "failed_count": self.failed_count,
                "exhausted_count": self.exhausted_count,
                "results": [item.to_dict() for item in self.results],
            }
        )
        return payload
