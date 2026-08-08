from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .results import CampaignResultRecord
from .validation import require_text


class AnalysisDisposition(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INDETERMINATE = "indeterminate"
    PROVIDER_ERROR = "provider_error"


@dataclass(frozen=True, slots=True)
class BehavioralAnalysisOutcome:
    disposition: AnalysisDisposition
    score: float | None = None
    confidence: float | None = None
    parsed_value: Any = None
    evaluator_id: str = "behavioral-analysis"
    metrics: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.disposition, AnalysisDisposition):
            try:
                object.__setattr__(
                    self,
                    "disposition",
                    AnalysisDisposition(self.disposition),
                )
            except Exception as exc:
                raise ValidationError("invalid analysis disposition.") from exc

        for name in ("score", "confidence"):
            value = getattr(self, name)
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValidationError(f"{name} must be numeric or None.")
                object.__setattr__(self, name, float(value))

        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValidationError("confidence must be between 0 and 1.")

        object.__setattr__(
            self,
            "evaluator_id",
            require_text("evaluator_id", self.evaluator_id),
        )

        if not isinstance(self.metrics, Mapping):
            raise ValidationError("metrics must be a mapping.")
        normalized_metrics: dict[str, float] = {}
        for key, value in self.metrics.items():
            key = require_text("metric name", key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError("metric values must be numeric.")
            normalized_metrics[key] = float(value)
        object.__setattr__(
            self,
            "metrics",
            dict(sorted(normalized_metrics.items())),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition.value,
            "score": self.score,
            "confidence": self.confidence,
            "parsed_value": self.parsed_value,
            "evaluator_id": self.evaluator_id,
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CampaignAnalysisRecord:
    analysis_id: str
    result_id: str
    result_sha256: str
    job_id: str
    case_id: str
    provider: str
    model: str
    outcome: BehavioralAnalysisOutcome
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "analysis_id",
            "result_id",
            "result_sha256",
            "job_id",
            "case_id",
            "provider",
            "model",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if not isinstance(self.outcome, BehavioralAnalysisOutcome):
            raise ValidationError("outcome must be BehavioralAnalysisOutcome.")

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h7.0",
            "result_id": self.result_id,
            "result_sha256": self.result_sha256,
            "job_id": self.job_id,
            "case_id": self.case_id,
            "provider": self.provider,
            "model": self.model,
            "outcome": self.outcome.identity_payload(),
            "metadata": dict(self.metadata),
        }

    @property
    def analysis_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["analysis_id"] = self.analysis_id
        payload["analysis_sha256"] = self.analysis_sha256
        return payload


@dataclass(frozen=True, slots=True)
class ProviderModelSummary:
    provider: str
    model: str
    observation_count: int
    passed_count: int
    failed_count: int
    indeterminate_count: int
    provider_error_count: int
    mean_score: float | None
    mean_confidence: float | None
    metrics: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", require_text("provider", self.provider))
        object.__setattr__(self, "model", require_text("model", self.model))

        for name in (
            "observation_count",
            "passed_count",
            "failed_count",
            "indeterminate_count",
            "provider_error_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValidationError(f"{name} must be a non-negative integer.")

        terminal = (
            self.passed_count
            + self.failed_count
            + self.indeterminate_count
            + self.provider_error_count
        )
        if terminal != self.observation_count:
            raise ValidationError(
                "summary disposition counts must equal observation_count."
            )

        for name in ("mean_score", "mean_confidence"):
            value = getattr(self, name)
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValidationError(f"{name} must be numeric or None.")
                object.__setattr__(self, name, float(value))

        if self.mean_confidence is not None and not 0.0 <= self.mean_confidence <= 1.0:
            raise ValidationError("mean_confidence must be between 0 and 1.")

        if not isinstance(self.metrics, Mapping):
            raise ValidationError("metrics must be a mapping.")
        normalized: dict[str, float] = {}
        for key, value in self.metrics.items():
            key = require_text("metric name", key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError("summary metric values must be numeric.")
            normalized[key] = float(value)
        object.__setattr__(self, "metrics", dict(sorted(normalized.items())))

    @property
    def pass_rate(self) -> float | None:
        if self.observation_count == 0:
            return None
        return self.passed_count / self.observation_count

    @property
    def provider_error_rate(self) -> float | None:
        if self.observation_count == 0:
            return None
        return self.provider_error_count / self.observation_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "observation_count": self.observation_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "indeterminate_count": self.indeterminate_count,
            "provider_error_count": self.provider_error_count,
            "pass_rate": self.pass_rate,
            "provider_error_rate": self.provider_error_rate,
            "mean_score": self.mean_score,
            "mean_confidence": self.mean_confidence,
            "metrics": dict(self.metrics),
        }


@dataclass(frozen=True, slots=True)
class CampaignAnalysisReport:
    report_id: str
    result_set_id: str
    result_set_sha256: str
    provenance_sha256: str
    analyses: tuple[CampaignAnalysisRecord, ...]
    summaries: tuple[ProviderModelSummary, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "report_id",
            "result_set_id",
            "result_set_sha256",
            "provenance_sha256",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        analyses = tuple(self.analyses)
        if any(not isinstance(item, CampaignAnalysisRecord) for item in analyses):
            raise ValidationError("analyses must contain CampaignAnalysisRecord values.")
        ids = tuple(item.analysis_id for item in analyses)
        if len(set(ids)) != len(ids):
            raise ValidationError("analyses contains duplicate analysis IDs.")
        object.__setattr__(
            self,
            "analyses",
            tuple(sorted(analyses, key=lambda item: (item.provider, item.model, item.job_id))),
        )

        summaries = tuple(self.summaries)
        if any(not isinstance(item, ProviderModelSummary) for item in summaries):
            raise ValidationError("summaries must contain ProviderModelSummary values.")
        keys = tuple((item.provider, item.model) for item in summaries)
        if len(set(keys)) != len(keys):
            raise ValidationError("summaries contains duplicate provider/model keys.")
        object.__setattr__(
            self,
            "summaries",
            tuple(sorted(summaries, key=lambda item: (item.provider, item.model))),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def observation_count(self) -> int:
        return len(self.analyses)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h7.0",
            "result_set_id": self.result_set_id,
            "result_set_sha256": self.result_set_sha256,
            "provenance_sha256": self.provenance_sha256,
            "analysis_sha256s": [item.analysis_sha256 for item in self.analyses],
            "summaries": [item.to_dict() for item in self.summaries],
            "metadata": dict(self.metadata),
        }

    @property
    def report_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "report_id": self.report_id,
                "report_sha256": self.report_sha256,
                "observation_count": self.observation_count,
                "analyses": [item.to_dict() for item in self.analyses],
            }
        )
        return payload
