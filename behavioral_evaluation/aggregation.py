from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from kernel.exceptions import ValidationError

from .contracts import BehavioralEvaluationRecord
from .metrics import (
    CaseBehaviorMetrics,
    calibration_error_pct,
    case_behavior_metrics,
    latency_statistics,
    mean_score,
    pass_rate_pct,
    provider_error_rate_pct,
    stable_answer_key,
    token_statistics,
)


@dataclass(frozen=True, slots=True)
class ProviderBehaviorMetrics:
    provider: str
    model: str
    observations: int
    evaluated: int
    provider_errors: int
    pass_rate_pct: float | None
    mean_score: float | None
    provider_error_rate_pct: float | None
    calibration_error_pct: float | None
    mean_case_surface_consistency_pct: float | None
    mean_case_semantic_consistency_pct: float | None
    mean_case_surface_entropy_bits: float | None
    mean_case_semantic_entropy_bits: float | None
    mean_latency_seconds: float | None
    median_latency_seconds: float | None
    p95_latency_seconds: float | None
    latency_tail_ratio: float | None
    total_tokens: int | None
    mean_tokens: float | None
    token_efficiency: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g5.0",
            **asdict(self),
        }


@dataclass(frozen=True, slots=True)
class CrossModelAgreement:
    provider_a: str
    model_a: str
    provider_b: str
    model_b: str
    matched_trials: int
    surface_agreement_pct: float | None
    semantic_agreement_pct: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g5.0",
            **asdict(self),
        }


@dataclass(frozen=True, slots=True)
class BehavioralMetricsReport:
    case_metrics: tuple[CaseBehaviorMetrics, ...]
    provider_metrics: tuple[ProviderBehaviorMetrics, ...]
    cross_model_agreement: tuple[CrossModelAgreement, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g5.0",
            "case_metrics": [item.to_dict() for item in self.case_metrics],
            "provider_metrics": [
                item.to_dict() for item in self.provider_metrics
            ],
            "cross_model_agreement": [
                item.to_dict() for item in self.cross_model_agreement
            ],
        }


def _weighted_mean(
    rows: Iterable[CaseBehaviorMetrics],
    field: str,
) -> float | None:
    pairs = []
    for row in rows:
        value = getattr(row, field)
        if value is not None and row.evaluated > 0:
            pairs.append((float(value), row.evaluated))

    if not pairs:
        return None

    weight = sum(item[1] for item in pairs)
    return sum(value * count for value, count in pairs) / weight


def provider_behavior_metrics(
    records: Iterable[BehavioralEvaluationRecord],
) -> ProviderBehaviorMetrics:
    values = tuple(records)
    if not values:
        raise ValidationError(
            "provider_behavior_metrics requires at least one observation."
        )

    identity = {(record.provider, record.model) for record in values}
    if len(identity) != 1:
        raise ValidationError(
            "provider metrics require one provider/model group."
        )
    provider, model = next(iter(identity))

    grouped: dict[
        tuple[str, str],
        list[BehavioralEvaluationRecord],
    ] = {}
    for record in values:
        grouped.setdefault(
            (record.contract_id, record.case_id),
            [],
        ).append(record)

    case_rows = tuple(
        case_behavior_metrics(group)
        for _, group in sorted(grouped.items())
    )

    latency = latency_statistics(values)
    tokens = token_statistics(values)

    return ProviderBehaviorMetrics(
        provider=provider,
        model=model,
        observations=len(values),
        evaluated=sum(row.evaluated for row in case_rows),
        provider_errors=sum(row.provider_errors for row in case_rows),
        pass_rate_pct=pass_rate_pct(values),
        mean_score=mean_score(values),
        provider_error_rate_pct=provider_error_rate_pct(values),
        calibration_error_pct=calibration_error_pct(values),
        mean_case_surface_consistency_pct=_weighted_mean(
            case_rows,
            "surface_consistency_pct",
        ),
        mean_case_semantic_consistency_pct=_weighted_mean(
            case_rows,
            "semantic_consistency_pct",
        ),
        mean_case_surface_entropy_bits=_weighted_mean(
            case_rows,
            "surface_entropy_bits",
        ),
        mean_case_semantic_entropy_bits=_weighted_mean(
            case_rows,
            "semantic_entropy_bits",
        ),
        mean_latency_seconds=latency["mean_latency_seconds"],
        median_latency_seconds=latency["median_latency_seconds"],
        p95_latency_seconds=latency["p95_latency_seconds"],
        latency_tail_ratio=latency["latency_tail_ratio"],
        total_tokens=tokens["total_tokens"],
        mean_tokens=tokens["mean_tokens"],
        token_efficiency=tokens["token_efficiency"],
    )


def cross_model_agreement(
    records: Iterable[BehavioralEvaluationRecord],
    *,
    provider_a: str,
    model_a: str,
    provider_b: str,
    model_b: str,
) -> CrossModelAgreement:
    values = tuple(records)

    def selected(provider: str, model: str):
        return [
            record
            for record in values
            if (
                record.provider == provider
                and record.model == model
                and record.evaluation_disposition.value == "evaluated"
            )
        ]

    a = selected(provider_a, model_a)
    b = selected(provider_b, model_b)

    def trial_key(record: BehavioralEvaluationRecord):
        return (
            record.contract_id,
            record.case_id,
            record.trial_index,
        )

    a_by_key = {trial_key(record): record for record in a}
    b_by_key = {trial_key(record): record for record in b}
    keys = sorted(set(a_by_key) & set(b_by_key))

    if not keys:
        return CrossModelAgreement(
            provider_a=provider_a,
            model_a=model_a,
            provider_b=provider_b,
            model_b=model_b,
            matched_trials=0,
            surface_agreement_pct=None,
            semantic_agreement_pct=None,
        )

    surface_matches = sum(
        stable_answer_key(a_by_key[key].surface_answer)
        == stable_answer_key(b_by_key[key].surface_answer)
        for key in keys
    )
    semantic_matches = sum(
        stable_answer_key(a_by_key[key].semantic_answer)
        == stable_answer_key(b_by_key[key].semantic_answer)
        for key in keys
    )

    return CrossModelAgreement(
        provider_a=provider_a,
        model_a=model_a,
        provider_b=provider_b,
        model_b=model_b,
        matched_trials=len(keys),
        surface_agreement_pct=100.0 * surface_matches / len(keys),
        semantic_agreement_pct=100.0 * semantic_matches / len(keys),
    )


def build_behavioral_metrics_report(
    records: Iterable[BehavioralEvaluationRecord],
) -> BehavioralMetricsReport:
    values = tuple(records)
    if not values:
        return BehavioralMetricsReport((), (), ())

    case_groups: dict[
        tuple[str, str, str, str],
        list[BehavioralEvaluationRecord],
    ] = {}
    provider_groups: dict[
        tuple[str, str],
        list[BehavioralEvaluationRecord],
    ] = {}

    for record in values:
        case_groups.setdefault(
            (
                record.provider,
                record.model,
                record.contract_id,
                record.case_id,
            ),
            [],
        ).append(record)
        provider_groups.setdefault(
            (record.provider, record.model),
            [],
        ).append(record)

    case_rows = tuple(
        case_behavior_metrics(case_groups[key])
        for key in sorted(case_groups)
    )
    provider_rows = tuple(
        provider_behavior_metrics(provider_groups[key])
        for key in sorted(provider_groups)
    )

    identities = sorted(provider_groups)
    agreements = []
    for index, (provider_a, model_a) in enumerate(identities):
        for provider_b, model_b in identities[index + 1:]:
            agreements.append(
                cross_model_agreement(
                    values,
                    provider_a=provider_a,
                    model_a=model_a,
                    provider_b=provider_b,
                    model_b=model_b,
                )
            )

    return BehavioralMetricsReport(
        case_metrics=case_rows,
        provider_metrics=provider_rows,
        cross_model_agreement=tuple(agreements),
    )
