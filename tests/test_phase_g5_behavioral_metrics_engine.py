import math

import pytest

from behavioral_evaluation import (
    BehavioralEvaluationRecord,
    EvaluationDisposition,
    ProviderExecutionStatus,
)
from behavioral_evaluation.aggregation import (
    build_behavioral_metrics_report,
    cross_model_agreement,
    provider_behavior_metrics,
)
from behavioral_evaluation.metrics import (
    answer_entropy_bits,
    calibration_error_pct,
    case_behavior_metrics,
    latency_statistics,
    modal_consistency_pct,
    normalized_answer_entropy,
    pass_rate_pct,
    percentile,
    provider_error_rate_pct,
    stable_answer_key,
    token_statistics,
)
from kernel.exceptions import ValidationError


def evaluated(
    *,
    observation_id,
    provider="openai",
    model="gpt-test",
    case_id="CASE-1",
    trial_index=1,
    passed=True,
    score=100.0,
    confidence=90,
    latency=1.0,
    total_tokens=100,
    surface="4",
    semantic=4,
    contract_id="prime-gap.numeric-exact",
):
    return BehavioralEvaluationRecord(
        observation_id=observation_id,
        contract_id=contract_id,
        case_id=case_id,
        trial_index=trial_index,
        provider=provider,
        model=model,
        execution_status=ProviderExecutionStatus.COMPLETED,
        evaluation_disposition=EvaluationDisposition.EVALUATED,
        passed=passed,
        score=score,
        confidence=confidence,
        latency_seconds=latency,
        total_tokens=total_tokens,
        surface_answer=surface,
        semantic_answer=semantic,
    )


def provider_error(
    *,
    observation_id,
    provider="openai",
    model="gpt-test",
    case_id="CASE-1",
    trial_index=1,
    contract_id="prime-gap.numeric-exact",
):
    return BehavioralEvaluationRecord(
        observation_id=observation_id,
        contract_id=contract_id,
        case_id=case_id,
        trial_index=trial_index,
        provider=provider,
        model=model,
        execution_status=ProviderExecutionStatus.PROVIDER_ERROR,
        evaluation_disposition=EvaluationDisposition.NOT_EVALUATED,
        provider_error_category="timeout",
    )


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4, 5], 0.95) == 4.8


def test_percentile_empty():
    assert percentile([], 0.95) is None


def test_percentile_rejects_invalid_q():
    with pytest.raises(ValidationError):
        percentile([1], 1.1)


def test_stable_answer_key_normalizes_mapping_order():
    assert stable_answer_key({"b": 2, "a": 1}) == stable_answer_key(
        {"a": 1, "b": 2}
    )


def test_entropy_zero_for_stable_answers():
    assert answer_entropy_bits([4, 4, 4]) == 0.0


def test_entropy_one_bit_for_balanced_binary_answers():
    assert answer_entropy_bits([4, 4, 6, 6]) == 1.0


def test_normalized_entropy_zero_for_stable_answers():
    assert normalized_answer_entropy([4, 4, 4]) == 0.0


def test_normalized_entropy_one_for_balanced_binary_answers():
    assert normalized_answer_entropy([4, 4, 6, 6]) == 1.0


def test_modal_consistency():
    assert modal_consistency_pct([4, 4, 6]) == pytest.approx(66.6666667)


def test_pass_rate_ignores_provider_errors():
    records = (
        evaluated(observation_id="OBS-" + "A" * 24, passed=True),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            trial_index=2,
            passed=False,
            score=0,
        ),
        provider_error(
            observation_id="OBS-" + "C" * 24,
            trial_index=3,
        ),
    )
    assert pass_rate_pct(records) == 50.0


def test_provider_error_rate_uses_all_observations():
    records = (
        evaluated(observation_id="OBS-" + "A" * 24),
        provider_error(
            observation_id="OBS-" + "B" * 24,
            trial_index=2,
        ),
    )
    assert provider_error_rate_pct(records) == 50.0


def test_calibration_error_perfect():
    records = (
        evaluated(
            observation_id="OBS-" + "A" * 24,
            confidence=100,
            passed=True,
        ),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            trial_index=2,
            confidence=0,
            passed=False,
            score=0,
        ),
    )
    assert calibration_error_pct(records) == 0.0


def test_calibration_error_detects_overconfidence():
    records = (
        evaluated(
            observation_id="OBS-" + "A" * 24,
            confidence=100,
            passed=False,
            score=0,
        ),
    )
    assert calibration_error_pct(records) == 100.0


def test_latency_statistics():
    records = tuple(
        evaluated(
            observation_id=f"OBS-{i:024d}",
            trial_index=i,
            latency=float(i),
        )
        for i in range(1, 6)
    )
    stats = latency_statistics(records)
    assert stats["mean_latency_seconds"] == 3.0
    assert stats["median_latency_seconds"] == 3.0
    assert stats["p95_latency_seconds"] == 4.8
    assert stats["latency_tail_ratio"] == pytest.approx(1.6)


def test_token_efficiency():
    records = (
        evaluated(
            observation_id="OBS-" + "A" * 24,
            total_tokens=100,
        ),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            trial_index=2,
            total_tokens=100,
        ),
    )
    stats = token_statistics(records)
    assert stats["total_tokens"] == 200
    assert stats["mean_tokens"] == 100
    assert stats["token_efficiency"] == 1000.0


def test_case_metrics_surface_vs_semantic_stability():
    records = (
        evaluated(
            observation_id="OBS-" + "A" * 24,
            surface='{"prediction":4}',
            semantic=4,
        ),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            trial_index=2,
            surface='{"prediction": 4}',
            semantic=4,
        ),
    )
    metrics = case_behavior_metrics(records)
    assert metrics.surface_consistency_pct == 50.0
    assert metrics.semantic_consistency_pct == 100.0
    assert metrics.surface_entropy_bits == 1.0
    assert metrics.semantic_entropy_bits == 0.0


def test_case_metrics_provider_error_does_not_pollute_entropy():
    records = (
        evaluated(observation_id="OBS-" + "A" * 24, semantic=4),
        provider_error(
            observation_id="OBS-" + "B" * 24,
            trial_index=2,
        ),
    )
    metrics = case_behavior_metrics(records)
    assert metrics.evaluated == 1
    assert metrics.provider_errors == 1
    assert metrics.semantic_entropy_bits == 0.0


def test_case_metrics_reject_mixed_cases():
    records = (
        evaluated(observation_id="OBS-" + "A" * 24, case_id="A"),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            trial_index=2,
            case_id="B",
        ),
    )
    with pytest.raises(ValidationError):
        case_behavior_metrics(records)


def test_provider_metrics_aggregate_case_entropy_not_pooled_answers():
    records = (
        evaluated(
            observation_id="OBS-" + "A" * 24,
            case_id="CASE-A",
            semantic=4,
        ),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            case_id="CASE-A",
            trial_index=2,
            semantic=4,
        ),
        evaluated(
            observation_id="OBS-" + "C" * 24,
            case_id="CASE-B",
            trial_index=1,
            semantic="alpha",
        ),
        evaluated(
            observation_id="OBS-" + "D" * 24,
            case_id="CASE-B",
            trial_index=2,
            semantic="alpha",
        ),
    )
    metrics = provider_behavior_metrics(records)
    assert metrics.mean_case_semantic_entropy_bits == 0.0
    assert metrics.mean_case_semantic_consistency_pct == 100.0


def test_provider_metrics_reject_mixed_models():
    records = (
        evaluated(observation_id="OBS-" + "A" * 24, model="a"),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            trial_index=2,
            model="b",
        ),
    )
    with pytest.raises(ValidationError):
        provider_behavior_metrics(records)


def agreement_records():
    return (
        evaluated(
            observation_id="OBS-" + "A" * 24,
            provider="openai",
            model="gpt",
            trial_index=1,
            surface="answer 4",
            semantic=4,
        ),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            provider="deepseek",
            model="ds",
            trial_index=1,
            surface="4",
            semantic=4,
        ),
        evaluated(
            observation_id="OBS-" + "C" * 24,
            provider="openai",
            model="gpt",
            trial_index=2,
            surface="6",
            semantic=6,
        ),
        evaluated(
            observation_id="OBS-" + "D" * 24,
            provider="deepseek",
            model="ds",
            trial_index=2,
            surface="4",
            semantic=4,
        ),
    )


def test_cross_model_surface_and_semantic_agreement():
    result = cross_model_agreement(
        agreement_records(),
        provider_a="openai",
        model_a="gpt",
        provider_b="deepseek",
        model_b="ds",
    )
    assert result.matched_trials == 2
    assert result.surface_agreement_pct == 0.0
    assert result.semantic_agreement_pct == 50.0


def test_cross_model_agreement_none_without_overlap():
    records = (
        evaluated(
            observation_id="OBS-" + "A" * 24,
            provider="openai",
            model="gpt",
            case_id="A",
        ),
        evaluated(
            observation_id="OBS-" + "B" * 24,
            provider="deepseek",
            model="ds",
            case_id="B",
        ),
    )
    result = cross_model_agreement(
        records,
        provider_a="openai",
        model_a="gpt",
        provider_b="deepseek",
        model_b="ds",
    )
    assert result.matched_trials == 0
    assert result.semantic_agreement_pct is None


def test_cross_model_agreement_ignores_provider_errors():
    records = (
        evaluated(
            observation_id="OBS-" + "A" * 24,
            provider="openai",
            model="gpt",
            semantic=4,
        ),
        provider_error(
            observation_id="OBS-" + "B" * 24,
            provider="deepseek",
            model="ds",
        ),
    )
    result = cross_model_agreement(
        records,
        provider_a="openai",
        model_a="gpt",
        provider_b="deepseek",
        model_b="ds",
    )
    assert result.matched_trials == 0


def test_report_is_deterministic():
    records = agreement_records()
    a = build_behavioral_metrics_report(records).to_dict()
    b = build_behavioral_metrics_report(tuple(reversed(records))).to_dict()
    assert a == b


def test_report_contains_case_provider_and_agreement_sections():
    report = build_behavioral_metrics_report(agreement_records())
    assert len(report.case_metrics) == 2
    assert len(report.provider_metrics) == 2
    assert len(report.cross_model_agreement) == 1


def test_empty_report_is_valid():
    report = build_behavioral_metrics_report(())
    assert report.case_metrics == ()
    assert report.provider_metrics == ()
    assert report.cross_model_agreement == ()


def test_case_metric_schema_version():
    row = case_behavior_metrics(
        (evaluated(observation_id="OBS-" + "A" * 24),)
    )
    assert row.to_dict()["schema_version"] == "g5.0"


def test_provider_metric_schema_version():
    row = provider_behavior_metrics(
        (evaluated(observation_id="OBS-" + "A" * 24),)
    )
    assert row.to_dict()["schema_version"] == "g5.0"


def test_report_schema_version():
    assert build_behavioral_metrics_report(()).to_dict()["schema_version"] == "g5.0"

