"""Immutable data models for deterministic experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


class ExperimentStatus(str, Enum):
    """Lifecycle states for an experiment."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ExperimentSpecification:
    """Canonical scientific definition of one experiment.

    The deterministic experiment identifier is derived from the canonical
    serialization of this specification. Runtime timestamps and mutable
    state are deliberately excluded from the specification.
    """

    name: str
    sequence_plugin: str
    sequence_parameters: Mapping[str, Any]
    window_sizes: tuple[int, ...]
    case_count: int
    prompt_template: str
    model_provider: str
    model_name: str
    model_parameters: Mapping[str, Any] = field(default_factory=dict)
    random_seed: int = 0
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Experiment name must not be empty.")

        if not self.sequence_plugin.strip():
            raise ValueError("sequence_plugin must not be empty.")

        if not self.window_sizes:
            raise ValueError("At least one observation window size is required.")

        if any(size <= 0 for size in self.window_sizes):
            raise ValueError("All observation window sizes must be positive.")

        if len(set(self.window_sizes)) != len(self.window_sizes):
            raise ValueError("Observation window sizes must be unique.")

        if self.case_count <= 0:
            raise ValueError("case_count must be positive.")

        if not self.prompt_template.strip():
            raise ValueError("prompt_template must not be empty.")

        if not self.model_provider.strip():
            raise ValueError("model_provider must not be empty.")

        if not self.model_name.strip():
            raise ValueError("model_name must not be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        result = asdict(self)
        result["window_sizes"] = list(self.window_sizes)
        return result


@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    """One append-only model response and evaluation record."""

    case_id: str
    sequence_index: int
    window_size: int
    prompt_sha256: str
    response_text: str
    parsed_prediction: int | None
    actual_value: int | None
    is_correct: bool | None
    confidence: int | None
    latency_seconds: float | None
    provider_request_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
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

        if self.confidence is not None and not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100.")

        if self.latency_seconds is not None and self.latency_seconds < 0:
            raise ValueError("latency_seconds must be non-negative.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExperimentCheckpoint:
    """Restart position for a partially executed experiment."""

    next_case_number: int
    completed_case_count: int
    failed_case_count: int
    last_case_id: str | None
    updated_at_utc: str

    def __post_init__(self) -> None:
        if self.next_case_number < 0:
            raise ValueError("next_case_number must be non-negative.")

        if self.completed_case_count < 0:
            raise ValueError("completed_case_count must be non-negative.")

        if self.failed_case_count < 0:
            raise ValueError("failed_case_count must be non-negative.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExperimentState:
    """Mutable experiment lifecycle state stored independently of the spec."""

    experiment_id: str
    status: ExperimentStatus
    created_at_utc: str
    updated_at_utc: str
    started_at_utc: str | None = None
    completed_at_utc: str | None = None
    failure_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result
