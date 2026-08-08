from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from kernel.exceptions import ValidationError

from .analysis_contracts import (
    AnalysisDisposition,
    BehavioralAnalysisOutcome,
    CampaignAnalysisReport,
)
from .identity import canonical_metadata, sha256_json
from .result_assembly import CampaignAssembly
from .results import CampaignResultRecord
from .validation import require_text


class FrozenBehavioralEvaluator(Protocol):
    def __call__(self, result: CampaignResultRecord) -> Any:
        ...


def _extract(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _enum_text(value: Any) -> str:
    if value is None:
        return ""
    raw = getattr(value, "value", value)
    return str(raw).strip().lower()


def _normalize_disposition(value: Any) -> AnalysisDisposition:
    token = _enum_text(value).replace("-", "_").replace(" ", "_")

    passed = {
        "pass",
        "passed",
        "success",
        "successful",
        "correct",
        "accepted",
    }
    failed = {
        "fail",
        "failed",
        "failure",
        "incorrect",
        "rejected",
    }
    indeterminate = {
        "indeterminate",
        "unknown",
        "unscored",
        "not_scored",
        "not_evaluated",
        "parse_error",
    }
    provider_error = {
        "provider_error",
        "execution_error",
        "provider_failure",
        "runtime_error",
    }

    if token in passed:
        return AnalysisDisposition.PASSED
    if token in failed:
        return AnalysisDisposition.FAILED
    if token in provider_error:
        return AnalysisDisposition.PROVIDER_ERROR
    if token in indeterminate:
        return AnalysisDisposition.INDETERMINATE

    raise ValidationError(
        f"Unsupported frozen behavioral disposition: {value!r}"
    )


def _normalize_confidence(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("behavioral confidence must be numeric or None.")

    numeric = float(value)
    if 0.0 <= numeric <= 1.0:
        return numeric
    if 0.0 <= numeric <= 100.0:
        return numeric / 100.0
    raise ValidationError(
        "behavioral confidence must be in [0,1] or [0,100]."
    )


def _normalize_score(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("behavioral score must be numeric or None.")
    return float(value)


def _normalize_metrics(value: Any) -> dict[str, float]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValidationError("behavioral metrics must be a mapping.")

    normalized: dict[str, float] = {}
    for key, metric in value.items():
        key = require_text("metric name", key)
        if isinstance(metric, bool) or not isinstance(metric, (int, float)):
            raise ValidationError("behavioral metric values must be numeric.")
        normalized[key] = float(metric)
    return dict(sorted(normalized.items()))


@dataclass(frozen=True, slots=True)
class FrozenGBehavioralAdapter:
    evaluator: FrozenBehavioralEvaluator | Callable[[CampaignResultRecord], Any]
    evaluator_id: str = "phase-g.frozen"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not callable(self.evaluator):
            raise ValidationError("evaluator must be callable.")
        object.__setattr__(
            self,
            "evaluator_id",
            require_text("evaluator_id", self.evaluator_id),
        )
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def __call__(self, result: CampaignResultRecord) -> BehavioralAnalysisOutcome:
        if not isinstance(result, CampaignResultRecord):
            raise ValidationError("result must be CampaignResultRecord.")

        raw = self.evaluator(result)

        disposition = _normalize_disposition(
            _extract(raw, "disposition", _extract(raw, "status"))
        )
        score = _normalize_score(
            _extract(raw, "score", _extract(raw, "evaluation_score"))
        )
        confidence = _normalize_confidence(
            _extract(raw, "confidence")
        )
        parsed_value = _extract(
            raw,
            "parsed_value",
            _extract(raw, "prediction"),
        )
        metrics = _normalize_metrics(
            _extract(raw, "metrics", {})
        )

        raw_evaluator_id = _extract(
            raw,
            "evaluator_id",
            self.evaluator_id,
        )

        return BehavioralAnalysisOutcome(
            disposition=disposition,
            score=score,
            confidence=confidence,
            parsed_value=parsed_value,
            evaluator_id=require_text("evaluator_id", raw_evaluator_id),
            metrics=metrics,
            metadata={
                "adapter": "FrozenGBehavioralAdapter",
                "phase_g_contract": self.evaluator_id,
                **dict(self.metadata),
            },
        )


@dataclass(frozen=True, slots=True)
class ScientificIntegrationRecord:
    integration_id: str
    result_set_id: str
    result_set_sha256: str
    provenance_sha256: str
    analysis_report_id: str
    analysis_report_sha256: str
    adapter_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "integration_id",
            "result_set_id",
            "result_set_sha256",
            "provenance_sha256",
            "analysis_report_id",
            "analysis_report_sha256",
            "adapter_id",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h8.0",
            "result_set_id": self.result_set_id,
            "result_set_sha256": self.result_set_sha256,
            "provenance_sha256": self.provenance_sha256,
            "analysis_report_id": self.analysis_report_id,
            "analysis_report_sha256": self.analysis_report_sha256,
            "adapter_id": self.adapter_id,
            "metadata": dict(self.metadata),
        }

    @property
    def integration_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["integration_id"] = self.integration_id
        payload["integration_sha256"] = self.integration_sha256
        return payload


def build_scientific_integration_record(
    *,
    assembly: CampaignAssembly,
    analysis_report: CampaignAnalysisReport,
    adapter_id: str,
    metadata: Mapping[str, Any] | None = None,
) -> ScientificIntegrationRecord:
    if not isinstance(assembly, CampaignAssembly):
        raise ValidationError("assembly must be CampaignAssembly.")
    if not isinstance(analysis_report, CampaignAnalysisReport):
        raise ValidationError("analysis_report must be CampaignAnalysisReport.")

    if analysis_report.result_set_id != assembly.result_set.result_set_id:
        raise ValidationError("analysis report result_set_id mismatch.")
    if analysis_report.result_set_sha256 != assembly.result_set.result_set_sha256:
        raise ValidationError("analysis report result_set_sha256 mismatch.")
    if analysis_report.provenance_sha256 != assembly.provenance.provenance_sha256:
        raise ValidationError("analysis report provenance_sha256 mismatch.")

    adapter_id = require_text("adapter_id", adapter_id)

    seed = {
        "schema_version": "h8.0",
        "result_set_sha256": assembly.result_set.result_set_sha256,
        "provenance_sha256": assembly.provenance.provenance_sha256,
        "analysis_report_sha256": analysis_report.report_sha256,
        "adapter_id": adapter_id,
    }

    return ScientificIntegrationRecord(
        integration_id=f"INTEGRATION-{sha256_json(seed)[:20].upper()}",
        result_set_id=assembly.result_set.result_set_id,
        result_set_sha256=assembly.result_set.result_set_sha256,
        provenance_sha256=assembly.provenance.provenance_sha256,
        analysis_report_id=analysis_report.report_id,
        analysis_report_sha256=analysis_report.report_sha256,
        adapter_id=adapter_id,
        metadata=dict(metadata or {}),
    )
