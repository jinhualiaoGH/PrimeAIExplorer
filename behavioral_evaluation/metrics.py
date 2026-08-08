from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from kernel.exceptions import ValidationError

from .contracts import (
    BehavioralEvaluationRecord,
    EvaluationDisposition,
    ProviderExecutionStatus,
)


def _records(
    values: Iterable[BehavioralEvaluationRecord],
) -> tuple[BehavioralEvaluationRecord, ...]:
    records = tuple(values)
    for record in records:
        if not isinstance(record, BehavioralEvaluationRecord):
            raise ValidationError(
                "metrics require BehavioralEvaluationRecord values."
            )
    return records


def _mean(values: Sequence[float]) -> float | None:
    return statistics.mean(values) if values else None


def _median(values: Sequence[float]) -> float | None:
    return statistics.median(values) if values else None


def percentile(values: Sequence[float], q: float) -> float | None:
    if not 0.0 <= q <= 1.0:
        raise ValidationError("percentile q must be from 0 to 1.")
    if not values:
        return None

    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def stable_answer_key(value: Any) -> str:
    """Produce a deterministic answer key for entropy/agreement metrics."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError):
        return repr(value)


def answer_entropy_bits(values: Sequence[Any]) -> float | None:
    if not values:
        return None

    keys = [stable_answer_key(value) for value in values]
    counts = Counter(keys)
    n = len(keys)

    entropy = 0.0
    for count in counts.values():
        p = count / n
        entropy -= p * math.log2(p)
    return entropy


def normalized_answer_entropy(values: Sequence[Any]) -> float | None:
    if not values:
        return None

    distinct = len({stable_answer_key(value) for value in values})
    if distinct <= 1:
        return 0.0

    entropy = answer_entropy_bits(values)
    assert entropy is not None
    return entropy / math.log2(distinct)


def modal_consistency_pct(values: Sequence[Any]) -> float | None:
    if not values:
        return None

    keys = [stable_answer_key(value) for value in values]
    count = Counter(keys).most_common(1)[0][1]
    return 100.0 * count / len(keys)


def calibration_error_pct(
    records: Iterable[BehavioralEvaluationRecord],
) -> float | None:
    usable = []
    for record in _records(records):
        if (
            record.evaluation_disposition is EvaluationDisposition.EVALUATED
            and isinstance(record.passed, bool)
            and record.confidence is not None
        ):
            target = 1.0 if record.passed else 0.0
            usable.append(abs(record.confidence / 100.0 - target))

    return 100.0 * statistics.mean(usable) if usable else None


def provider_error_rate_pct(
    records: Iterable[BehavioralEvaluationRecord],
) -> float | None:
    values = _records(records)
    if not values:
        return None
    errors = sum(
        record.execution_status is ProviderExecutionStatus.PROVIDER_ERROR
        for record in values
    )
    return 100.0 * errors / len(values)


def pass_rate_pct(
    records: Iterable[BehavioralEvaluationRecord],
) -> float | None:
    evaluated = [
        record
        for record in _records(records)
        if record.evaluation_disposition is EvaluationDisposition.EVALUATED
    ]
    if not evaluated:
        return None

    passed = sum(record.passed is True for record in evaluated)
    return 100.0 * passed / len(evaluated)


def mean_score(
    records: Iterable[BehavioralEvaluationRecord],
) -> float | None:
    scores = [
        float(record.score)
        for record in _records(records)
        if (
            record.evaluation_disposition is EvaluationDisposition.EVALUATED
            and record.score is not None
        )
    ]
    return _mean(scores)


def latency_statistics(
    records: Iterable[BehavioralEvaluationRecord],
) -> dict[str, float | None]:
    latencies = [
        float(record.latency_seconds)
        for record in _records(records)
        if record.latency_seconds is not None
    ]

    mean_value = _mean(latencies)
    median_value = _median(latencies)
    p95_value = percentile(latencies, 0.95)

    if median_value in (None, 0.0) or p95_value is None:
        tail_ratio = None
    else:
        tail_ratio = p95_value / median_value

    return {
        "mean_latency_seconds": mean_value,
        "median_latency_seconds": median_value,
        "p95_latency_seconds": p95_value,
        "latency_tail_ratio": tail_ratio,
    }


def token_statistics(
    records: Iterable[BehavioralEvaluationRecord],
) -> dict[str, float | int | None]:
    values = _records(records)
    totals = [
        record.total_tokens
        for record in values
        if record.total_tokens is not None
    ]

    total_tokens = sum(totals) if totals else None
    mean_tokens = statistics.mean(totals) if totals else None
    pass_rate = pass_rate_pct(values)

    if mean_tokens in (None, 0) or pass_rate is None:
        efficiency = None
    else:
        # Pass-rate percentage points per 1,000 mean tokens.
        efficiency = pass_rate * 1000.0 / mean_tokens

    return {
        "total_tokens": total_tokens,
        "mean_tokens": mean_tokens,
        "token_efficiency": efficiency,
    }


@dataclass(frozen=True, slots=True)
class CaseBehaviorMetrics:
    provider: str
    model: str
    contract_id: str
    case_id: str
    observations: int
    evaluated: int
    provider_errors: int
    pass_rate_pct: float | None
    mean_score: float | None
    provider_error_rate_pct: float | None
    calibration_error_pct: float | None
    surface_consistency_pct: float | None
    semantic_consistency_pct: float | None
    surface_distinct_answers: int
    semantic_distinct_answers: int
    surface_entropy_bits: float | None
    semantic_entropy_bits: float | None
    surface_normalized_entropy: float | None
    semantic_normalized_entropy: float | None
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


def case_behavior_metrics(
    records: Iterable[BehavioralEvaluationRecord],
) -> CaseBehaviorMetrics:
    values = _records(records)
    if not values:
        raise ValidationError(
            "case_behavior_metrics requires at least one observation."
        )

    identity = {
        (
            record.provider,
            record.model,
            record.contract_id,
            record.case_id,
        )
        for record in values
    }
    if len(identity) != 1:
        raise ValidationError(
            "case metrics require one provider/model/contract/case group."
        )

    provider, model, contract_id, case_id = next(iter(identity))

    evaluated = [
        record
        for record in values
        if record.evaluation_disposition is EvaluationDisposition.EVALUATED
    ]
    surface_answers = [record.surface_answer for record in evaluated]
    semantic_answers = [record.semantic_answer for record in evaluated]

    latency = latency_statistics(values)
    tokens = token_statistics(values)

    return CaseBehaviorMetrics(
        provider=provider,
        model=model,
        contract_id=contract_id,
        case_id=case_id,
        observations=len(values),
        evaluated=len(evaluated),
        provider_errors=sum(
            record.execution_status is ProviderExecutionStatus.PROVIDER_ERROR
            for record in values
        ),
        pass_rate_pct=pass_rate_pct(values),
        mean_score=mean_score(values),
        provider_error_rate_pct=provider_error_rate_pct(values),
        calibration_error_pct=calibration_error_pct(values),
        surface_consistency_pct=modal_consistency_pct(surface_answers),
        semantic_consistency_pct=modal_consistency_pct(semantic_answers),
        surface_distinct_answers=len(
            {stable_answer_key(value) for value in surface_answers}
        ),
        semantic_distinct_answers=len(
            {stable_answer_key(value) for value in semantic_answers}
        ),
        surface_entropy_bits=answer_entropy_bits(surface_answers),
        semantic_entropy_bits=answer_entropy_bits(semantic_answers),
        surface_normalized_entropy=normalized_answer_entropy(surface_answers),
        semantic_normalized_entropy=normalized_answer_entropy(semantic_answers),
        mean_latency_seconds=latency["mean_latency_seconds"],
        median_latency_seconds=latency["median_latency_seconds"],
        p95_latency_seconds=latency["p95_latency_seconds"],
        latency_tail_ratio=latency["latency_tail_ratio"],
        total_tokens=tokens["total_tokens"],
        mean_tokens=tokens["mean_tokens"],
        token_efficiency=tokens["token_efficiency"],
    )
