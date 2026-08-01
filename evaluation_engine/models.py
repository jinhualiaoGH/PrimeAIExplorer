from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256


def _text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be text.")
    value = value.strip()
    if not value:
        raise ValidationError(f"{name} must not be empty.")
    return value


def _number(name: str, value: int | float) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be numeric.")
    return value


@dataclass(frozen=True)
class RawModelResponse:
    prompt_id: str
    response_text: str
    model_id: str = "unspecified"
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "prompt_id", _text("prompt_id", self.prompt_id))
        object.__setattr__(self, "response_text", _text("response_text", self.response_text))
        object.__setattr__(self, "model_id", _text("model_id", self.model_id))
        metadata = {} if self.metadata is None else self.metadata
        if not isinstance(metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", dict(metadata))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RawModelResponse":
        if not isinstance(payload, Mapping):
            raise ValidationError("raw response must be a mapping.")
        required = {"prompt_id", "response_text"}
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(f"raw response is missing fields: {missing}")
        return cls(
            prompt_id=payload["prompt_id"],
            response_text=payload["response_text"],
            model_id=payload.get("model_id", "unspecified"),
            metadata=payload.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "response_text": self.response_text,
            "model_id": self.model_id,
            "metadata": dict(self.metadata or {}),
        }

    @property
    def response_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class ParsedPrediction:
    prediction: int | float
    confidence: int
    explanation: str
    raw_payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "prediction", _number("prediction", self.prediction))
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, int):
            raise ValidationError("confidence must be an integer.")
        if not 0 <= self.confidence <= 100:
            raise ValidationError("confidence must be from 0 to 100.")
        object.__setattr__(self, "explanation", _text("explanation", self.explanation))
        if not isinstance(self.raw_payload, Mapping):
            raise ValidationError("raw_payload must be a mapping.")
        object.__setattr__(self, "raw_payload", dict(self.raw_payload))

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction": self.prediction,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "raw_payload": dict(self.raw_payload),
        }

    @property
    def parsed_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class EvaluationRecord:
    schema_version: str
    evaluation_id: str
    evaluation_sha256: str
    prompt_id: str
    prompt_sha256: str
    response_sha256: str
    model_id: str
    prediction: int | float
    target: int | float
    confidence: int
    explanation: str
    exact_match: bool
    absolute_error: float
    squared_error: float
    confidence_error: float
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in (
            "schema_version",
            "evaluation_id",
            "prompt_id",
            "model_id",
            "explanation",
        ):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        for name in ("evaluation_sha256", "prompt_sha256", "response_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 64:
                raise ValidationError(f"{name} must contain 64 characters.")
        object.__setattr__(self, "prediction", _number("prediction", self.prediction))
        object.__setattr__(self, "target", _number("target", self.target))
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, int):
            raise ValidationError("confidence must be an integer.")
        if not isinstance(self.exact_match, bool):
            raise ValidationError("exact_match must be boolean.")
        for name in ("absolute_error", "squared_error", "confidence_error"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError(f"{name} must be numeric.")
            if value < 0:
                raise ValidationError(f"{name} must be nonnegative.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evaluation_id": self.evaluation_id,
            "evaluation_sha256": self.evaluation_sha256,
            "prompt_id": self.prompt_id,
            "prompt_sha256": self.prompt_sha256,
            "response_sha256": self.response_sha256,
            "model_id": self.model_id,
            "prediction": self.prediction,
            "target": self.target,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "exact_match": self.exact_match,
            "absolute_error": self.absolute_error,
            "squared_error": self.squared_error,
            "confidence_error": self.confidence_error,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EvaluationBatch:
    records: tuple[EvaluationRecord, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))
        if not self.records:
            raise ValidationError("evaluation batch must not be empty.")
        ids = [record.evaluation_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValidationError("evaluation batch contains duplicate records.")

    @property
    def exact_match_count(self) -> int:
        return sum(record.exact_match for record in self.records)

    @property
    def exact_match_rate(self) -> float:
        return self.exact_match_count / len(self.records)

    @property
    def mean_absolute_error(self) -> float:
        return sum(record.absolute_error for record in self.records) / len(self.records)

    @property
    def root_mean_squared_error(self) -> float:
        return (
            sum(record.squared_error for record in self.records) / len(self.records)
        ) ** 0.5

    @property
    def mean_confidence(self) -> float:
        return sum(record.confidence for record in self.records) / len(self.records)

    @property
    def mean_confidence_error(self) -> float:
        return sum(record.confidence_error for record in self.records) / len(self.records)

    @property
    def batch_sha256(self) -> str:
        return stable_sha256([record.to_dict() for record in self.records])

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "records": [record.to_dict() for record in self.records],
            "summary": {
                "count": len(self.records),
                "exact_match_count": self.exact_match_count,
                "exact_match_rate": self.exact_match_rate,
                "mean_absolute_error": self.mean_absolute_error,
                "root_mean_squared_error": self.root_mean_squared_error,
                "mean_confidence": self.mean_confidence,
                "mean_confidence_error": self.mean_confidence_error,
            },
            "batch_sha256": self.batch_sha256,
        }
