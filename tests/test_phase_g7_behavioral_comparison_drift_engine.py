import pytest

from behavioral_evaluation import (
    DEFAULT_FINGERPRINT_SCHEMA,
    DriftThresholds,
    FingerprintBaseline,
    FingerprintBaselineRegistry,
    FingerprintBuilder,
    FingerprintSchema,
    ProviderBehaviorMetrics,
    build_comparison_matrix,
    compare_drift,
    compare_to_baseline,
)
from kernel.exceptions import ValidationError


def metrics(
    *,
    provider="openai",
    model="gpt-a",
    pass_rate=90.0,
    error_rate=5.0,
    calibration=10.0,
    semantic_consistency=95.0,
    semantic_entropy=0.2,
    median_latency=2.0,
):
    return ProviderBehaviorMetrics(
        provider=provider,
        model=model,
        observations=20,
        evaluated=19,
        provider_errors=1,
        pass_rate_pct=pass_rate,
        mean_score=pass_rate,
        provider_error_rate_pct=error_rate,
        calibration_error_pct=calibration,
        mean_case_surface_consistency_pct=80.0,
        mean_case_semantic_consistency_pct=semantic_consistency,
        mean_case_surface_entropy_bits=0.8,
        mean_case_semantic_entropy_bits=semantic_entropy,
        mean_latency_seconds=2.5,
        median_latency_seconds=median_latency,
        p95_latency_seconds=5.0,
        latency_tail_ratio=2.5,
        total_tokens=19000,
        mean_tokens=1000.0,
        token_efficiency=90.0,
    )


def fp(**kwargs):
    return FingerprintBuilder().build(metrics(**kwargs))


def test_threshold_default_classifications():
    thresholds = DriftThresholds()
    assert thresholds.classify(0.01) == "stable"
    assert thresholds.classify(0.10) == "minor"
    assert thresholds.classify(0.20) == "material"
    assert thresholds.classify(0.50) == "major"


def test_threshold_boundaries_are_inclusive():
    thresholds = DriftThresholds(0.05, 0.15, 0.30)
    assert thresholds.classify(0.05) == "stable"
    assert thresholds.classify(0.15) == "minor"
    assert thresholds.classify(0.30) == "material"


def test_thresholds_reject_nonmonotonic_values():
    with pytest.raises(ValidationError):
        DriftThresholds(0.2, 0.1, 0.3)


def test_baseline_requires_id():
    with pytest.raises(ValidationError):
        FingerprintBaseline("", fp())


def test_baseline_registry_names_are_sorted():
    registry = FingerprintBaselineRegistry(
        (
            FingerprintBaseline("z", fp(model="z")),
            FingerprintBaseline("a", fp(model="a")),
        )
    )
    assert registry.names() == ("a", "z")


def test_baseline_registry_rejects_duplicate():
    baseline = FingerprintBaseline("base", fp())
    registry = FingerprintBaselineRegistry((baseline,))
    with pytest.raises(ValidationError):
        registry.register(baseline)


def test_baseline_registry_get():
    baseline = FingerprintBaseline("base", fp())
    registry = FingerprintBaselineRegistry((baseline,))
    assert registry.get("base") == baseline


def test_identical_fingerprints_are_stable():
    baseline = fp()
    current = fp()
    report = compare_drift(baseline, current)
    assert report.aggregate_drift_score == 0.0
    assert report.classification == "stable"


def test_drift_report_counts_comparable_features():
    baseline = fp()
    current = fp(calibration=None)
    report = compare_drift(baseline, current)
    assert report.comparable_features == len(baseline.vector) - 1


def test_pass_rate_increase_is_improvement():
    baseline = fp(pass_rate=50.0)
    current = fp(pass_rate=100.0)
    report = compare_drift(baseline, current)
    feature = next(
        item for item in report.features
        if item.name == "pass_rate_pct"
    )
    assert feature.delta > 0
    assert feature.interpretation == "improvement"


def test_error_rate_increase_is_degradation():
    baseline = fp(error_rate=0.0)
    current = fp(error_rate=50.0)
    report = compare_drift(baseline, current)
    feature = next(
        item for item in report.features
        if item.name == "provider_error_rate_pct"
    )
    assert feature.delta < 0
    assert feature.interpretation == "degradation"


def test_latency_increase_is_degradation():
    baseline = fp(median_latency=1.0)
    current = fp(median_latency=10.0)
    report = compare_drift(baseline, current)
    feature = next(
        item for item in report.features
        if item.name == "median_latency_seconds"
    )
    assert feature.delta < 0
    assert feature.interpretation == "degradation"


def test_semantic_entropy_increase_is_degradation():
    baseline = fp(semantic_entropy=0.1)
    current = fp(semantic_entropy=1.0)
    report = compare_drift(baseline, current)
    feature = next(
        item for item in report.features
        if item.name == "mean_case_semantic_entropy_bits"
    )
    assert feature.delta < 0


def test_missing_feature_is_not_comparable():
    baseline = fp(calibration=None)
    current = fp(calibration=None)
    report = compare_drift(baseline, current)
    feature = next(
        item for item in report.features
        if item.name == "calibration_error_pct"
    )
    assert feature.delta is None
    assert feature.interpretation == "not_comparable"


def test_custom_thresholds_change_classification():
    baseline = fp(pass_rate=90.0)
    current = fp(pass_rate=80.0)
    loose = compare_drift(
        baseline,
        current,
        thresholds=DriftThresholds(1.0, 1.0, 1.0),
    )
    assert loose.classification == "stable"


def test_drift_rejects_schema_mismatch():
    custom_schema = FingerprintSchema(
        schema_id="custom",
        feature_names=("pass_rate_pct",),
        directions={"pass_rate_pct": "higher_is_better"},
        bounds={"pass_rate_pct": (0.0, 100.0)},
    )
    baseline = fp()
    current = FingerprintBuilder(custom_schema).build(metrics())
    with pytest.raises(ValidationError):
        compare_drift(baseline, current)


def test_drift_report_schema_version():
    report = compare_drift(fp(), fp())
    assert report.to_dict()["schema_version"] == "g7.0"


def test_matrix_empty_is_valid():
    matrix = build_comparison_matrix(())
    assert matrix.subjects == ()
    assert matrix.entries == ()


def test_matrix_subjects_are_sorted():
    matrix = build_comparison_matrix(
        (
            fp(provider="openai", model="z"),
            fp(provider="deepseek", model="a"),
        )
    )
    assert matrix.subjects == ("deepseek/a", "openai/z")


def test_matrix_has_n_squared_entries():
    matrix = build_comparison_matrix(
        (
            fp(provider="openai", model="a"),
            fp(provider="deepseek", model="b"),
            fp(provider="anthropic", model="c"),
        )
    )
    assert len(matrix.entries) == 9


def test_matrix_diagonal_distance_zero():
    matrix = build_comparison_matrix(
        (
            fp(provider="openai", model="a"),
            fp(provider="deepseek", model="b"),
        )
    )
    diagonal = [
        item for item in matrix.entries
        if item.row_subject == item.column_subject
    ]
    assert all(item.euclidean_distance == 0.0 for item in diagonal)


def test_matrix_is_symmetric_for_euclidean_distance():
    matrix = build_comparison_matrix(
        (
            fp(provider="openai", model="a", pass_rate=100),
            fp(provider="deepseek", model="b", pass_rate=50),
        )
    )
    entries = {
        (item.row_subject, item.column_subject): item
        for item in matrix.entries
    }
    assert (
        entries[("openai/a", "deepseek/b")].euclidean_distance
        == entries[("deepseek/b", "openai/a")].euclidean_distance
    )


def test_matrix_rejects_duplicate_subjects():
    with pytest.raises(ValidationError):
        build_comparison_matrix((fp(), fp()))


def test_matrix_rejects_mixed_schemas():
    custom_schema = FingerprintSchema(
        schema_id="custom",
        feature_names=("pass_rate_pct",),
        directions={"pass_rate_pct": "higher_is_better"},
        bounds={"pass_rate_pct": (0.0, 100.0)},
    )
    with pytest.raises(ValidationError):
        build_comparison_matrix(
            (
                fp(provider="openai", model="a"),
                FingerprintBuilder(custom_schema).build(
                    metrics(provider="deepseek", model="b")
                ),
            )
        )


def test_matrix_schema_version():
    matrix = build_comparison_matrix((fp(),))
    assert matrix.to_dict()["schema_version"] == "g7.0"


def test_compare_to_baseline_orders_reports_deterministically():
    baseline = FingerprintBaseline("base", fp(model="base"))
    registry = FingerprintBaselineRegistry((baseline,))
    report = compare_to_baseline(
        registry,
        "base",
        (
            fp(provider="openai", model="z"),
            fp(provider="deepseek", model="a"),
        ),
    )
    assert [item.current_model for item in report.reports] == ["a", "z"]


def test_compare_to_baseline_uses_named_baseline():
    baseline = FingerprintBaseline("base", fp(model="base"))
    registry = FingerprintBaselineRegistry((baseline,))
    report = compare_to_baseline(
        registry,
        "base",
        (fp(model="current"),),
    )
    assert report.baseline_id == "base"
    assert report.reports[0].baseline_model == "base"
    assert report.reports[0].current_model == "current"


def test_campaign_report_schema_version():
    baseline = FingerprintBaseline("base", fp(model="base"))
    registry = FingerprintBaselineRegistry((baseline,))
    report = compare_to_baseline(
        registry,
        "base",
        (fp(model="current"),),
    )
    assert report.to_dict()["schema_version"] == "g7.0"


def test_baseline_registry_schema_version():
    registry = FingerprintBaselineRegistry(
        (FingerprintBaseline("base", fp()),)
    )
    assert registry.to_dict()["schema_version"] == "g7.0"


def test_drift_score_is_dimension_independent_rms():
    baseline = fp(pass_rate=0.0)
    current = fp(pass_rate=100.0)
    report = compare_drift(baseline, current)
    changed = [
        item.absolute_delta
        for item in report.features
        if item.absolute_delta not in (None, 0.0)
    ]
    assert changed
    assert 0.0 < report.aggregate_drift_score <= 1.0
