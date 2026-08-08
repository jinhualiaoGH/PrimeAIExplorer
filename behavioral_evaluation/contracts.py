from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256


def _text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be text.")
    value = value.strip()
    if not value:
        raise ValidationError(f"{name} must not be empty.")
    return value


def _optional_text(name: str, value: str | None) -> str | None:
    return None if value is None else _text(name, value)


def _mapping(name: str, value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValidationError(f"{name} must be a mapping.")
    return dict(value)


class ProviderExecutionStatus(str, Enum):
    COMPLETED = "completed"
    PROVIDER_ERROR = "provider_error"


class EvaluationDisposition(str, Enum):
    EVALUATED = "evaluated"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True, slots=True)
class BehavioralEvaluationContract:
    contract_id: str
    evaluator_id: str
    contract_version: str = "1.0"
    canonicalizer_id: str | None = None
    requires_confidence: bool = False
    score_min: float = 0.0
    score_max: float = 100.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", _text("contract_id", self.contract_id))
        object.__setattr__(self, "evaluator_id", _text("evaluator_id", self.evaluator_id))
        object.__setattr__(self, "contract_version", _text("contract_version", self.contract_version))
        object.__setattr__(self, "canonicalizer_id", _optional_text("canonicalizer_id", self.canonicalizer_id))
        if not isinstance(self.requires_confidence, bool):
            raise ValidationError("requires_confidence must be boolean.")
        for name in ("score_min", "score_max"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError(f"{name} must be numeric.")
        if self.score_max <= self.score_min:
            raise ValidationError("score_max must be greater than score_min.")
        object.__setattr__(self, "metadata", _mapping("metadata", self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g1.0",
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "evaluator_id": self.evaluator_id,
            "canonicalizer_id": self.canonicalizer_id,
            "requires_confidence": self.requires_confidence,
            "score_min": self.score_min,
            "score_max": self.score_max,
            "metadata": dict(self.metadata),
        }

    @property
    def contract_sha256(self) -> str:
        return stable_sha256(self.to_dict())

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "BehavioralEvaluationContract":
        if not isinstance(payload, Mapping):
            raise ValidationError("evaluation contract must be a mapping.")
        required = {"contract_id", "evaluator_id"}
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(f"evaluation contract is missing fields: {missing}")
        return cls(
            contract_id=payload["contract_id"],
            evaluator_id=payload["evaluator_id"],
            contract_version=payload.get("contract_version", "1.0"),
            canonicalizer_id=payload.get("canonicalizer_id"),
            requires_confidence=payload.get("requires_confidence", False),
            score_min=payload.get("score_min", 0.0),
            score_max=payload.get("score_max", 100.0),
            metadata=payload.get("metadata", {}),
        )


@dataclass(frozen=True, slots=True)
class BehavioralEvaluationRecord:
    observation_id: str
    contract_id: str
    case_id: str
    trial_index: int
    provider: str
    model: str
    execution_status: ProviderExecutionStatus
    evaluation_disposition: EvaluationDisposition
    response_sha256: str | None = None
    passed: bool | None = None
    score: float | None = None
    confidence: int | None = None
    latency_seconds: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    provider_error_category: str | None = None
    provider_error_message: str | None = None
    surface_answer: Any = None
    semantic_answer: Any = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("observation_id", "contract_id", "case_id", "provider", "model"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))

        if isinstance(self.trial_index, bool) or not isinstance(self.trial_index, int) or self.trial_index <= 0:
            raise ValidationError("trial_index must be a positive integer.")

        try:
            status = ProviderExecutionStatus(self.execution_status)
            disposition = EvaluationDisposition(self.evaluation_disposition)
        except (TypeError, ValueError) as exc:
            raise ValidationError("invalid behavioral evaluation state.") from exc
        object.__setattr__(self, "execution_status", status)
        object.__setattr__(self, "evaluation_disposition", disposition)

        if self.response_sha256 is not None and (
            not isinstance(self.response_sha256, str) or len(self.response_sha256) != 64
        ):
            raise ValidationError("response_sha256 must contain 64 characters.")

        if self.confidence is not None and (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, int)
            or not 0 <= self.confidence <= 100
        ):
            raise ValidationError("confidence must be an integer from 0 to 100.")

        if self.latency_seconds is not None and (
            isinstance(self.latency_seconds, bool)
            or not isinstance(self.latency_seconds, (int, float))
            or self.latency_seconds < 0
        ):
            raise ValidationError("latency_seconds must be nonnegative numeric.")

        for name in ("input_tokens", "output_tokens", "total_tokens"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValidationError(f"{name} must be a nonnegative integer.")

        object.__setattr__(self, "provider_error_category", _optional_text("provider_error_category", self.provider_error_category))
        object.__setattr__(self, "provider_error_message", _optional_text("provider_error_message", self.provider_error_message))
        object.__setattr__(self, "metadata", _mapping("metadata", self.metadata))

        if status is ProviderExecutionStatus.PROVIDER_ERROR:
            if disposition is not EvaluationDisposition.NOT_EVALUATED:
                raise ValidationError("provider_error executions must be not_evaluated.")
            if self.passed is not None or self.score is not None:
                raise ValidationError("provider_error executions must not carry pass/score.")
            if self.provider_error_category is None:
                raise ValidationError("provider_error executions require provider_error_category.")
        else:
            if disposition is not EvaluationDisposition.EVALUATED:
                raise ValidationError("completed executions must be evaluated.")
            if not isinstance(self.passed, bool):
                raise ValidationError("evaluated executions require boolean passed.")
            if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
                raise ValidationError("evaluated executions require numeric score.")
            if not 0.0 <= float(self.score) <= 100.0:
                raise ValidationError("score must be from 0 to 100.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g1.0",
            "observation_id": self.observation_id,
            "contract_id": self.contract_id,
            "case_id": self.case_id,
            "trial_index": self.trial_index,
            "provider": self.provider,
            "model": self.model,
            "execution_status": self.execution_status.value,
            "evaluation_disposition": self.evaluation_disposition.value,
            "response_sha256": self.response_sha256,
            "passed": self.passed,
            "score": self.score,
            "confidence": self.confidence,
            "latency_seconds": self.latency_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "provider_error_category": self.provider_error_category,
            "provider_error_message": self.provider_error_message,
            "surface_answer": self.surface_answer,
            "semantic_answer": self.semantic_answer,
            "metadata": dict(self.metadata),
        }

    @property
    def record_sha256(self) -> str:
        return stable_sha256(self.to_dict())
