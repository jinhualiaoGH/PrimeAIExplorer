"""Models for deterministic checkpointed batch execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Retry configuration for one batch run."""

    max_attempts: int = 1
    delay_seconds: float = 0.0
    retry_exceptions: bool = True
    retry_unsuccessful_results: bool = False

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive.")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BatchCase:
    """One deterministic case scheduled for execution."""

    case_number: int
    case_id: str
    sequence_index: int
    window_size: int
    prompt_sha256: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.case_number < 0:
            raise ValueError("case_number must be non-negative.")
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty.")
        if self.sequence_index < 0:
            raise ValueError("sequence_index must be non-negative.")
        if self.window_size <= 0:
            raise ValueError("window_size must be positive.")
        if len(self.prompt_sha256) != 64:
            raise ValueError("prompt_sha256 must contain 64 hexadecimal characters.")
        try:
            int(self.prompt_sha256, 16)
        except ValueError as exc:
            raise ValueError("prompt_sha256 is not hexadecimal.") from exc

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BatchPlan:
    """Immutable ordered case plan for one experiment."""

    experiment_id: str
    cases: tuple[BatchCase, ...]
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    stop_on_failure: bool = False
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.experiment_id.startswith("EXP-"):
            raise ValueError("experiment_id must begin with 'EXP-'.")
        if not self.cases:
            raise ValueError("At least one case is required.")

        numbers = [case.case_number for case in self.cases]
        expected = list(range(len(self.cases)))
        if numbers != expected:
            raise ValueError(
                "Cases must be ordered and numbered consecutively from zero."
            )

        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case_id values must be unique.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "cases": [case.to_dict() for case in self.cases],
            "retry_policy": self.retry_policy.to_dict(),
            "stop_on_failure": self.stop_on_failure,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class CaseExecutionResult:
    """Normalized executor result for one case."""

    response_text: str
    parsed_prediction: int | None
    actual_value: int | None
    is_correct: bool | None
    confidence: int | None
    latency_seconds: float | None
    successful: bool = True
    provider_request_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100.")
        if self.latency_seconds is not None and self.latency_seconds < 0:
            raise ValueError("latency_seconds must be non-negative.")


@dataclass(frozen=True, slots=True)
class BatchRunSummary:
    """Summary returned by one runner invocation."""

    experiment_id: str
    starting_case_number: int
    ending_case_number: int
    attempted_count: int
    completed_count: int
    failed_count: int
    skipped_count: int
    interrupted: bool
    dry_run: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
