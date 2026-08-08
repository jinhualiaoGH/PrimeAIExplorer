import math

import pytest

from behavioral_evaluation import (
    DEFAULT_FINGERPRINT_SCHEMA,
    FingerprintBuilder,
    FingerprintNormalizer,
    FingerprintSchema,
    ProviderBehaviorMetrics,
    bounded_normalize,
    compare_fingerprints,
    cosine_similarity,
    euclidean_distance,
    manhattan_distance,
)
from kernel.exceptions import ValidationError


def metrics(
    *,
    provider="openai",
    model="gpt-test",
    pass_rate_pct=90.0,
    mean_score=90.0,
    provider_error_rate_pct=5.0,
    calibration_error_pct=10.0,
    surface_consistency=80.0,
    semantic_consistency=95.0,
    surface_entropy=0.8,
    semantic_entropy=0.2,
    median_latency=2.0,
    p95_latency=5.0,
    latency_tail_ratio=2.5,
    mean_tokens=1000.0,
    token_efficiency=90.0,
):
    return ProviderBehaviorMetrics(
        provider=provider,
        model=model,
        observations=20,
        evaluated=19,
        provider_errors=1,
        pass_rate_pct=pass_rate_pct,
        mean_score=mean_score,
        provider_error_rate_pct=provider_error_rate_pct,
        calibration_error_pct=calibration_error_pct,
        mean_case_surface_consistency_pct=surface_consistency,
        mean_case_semantic_consistency_pct=semantic_consistency,
        mean_case_surface_entropy_bits=surface_entropy,
        mean_case_semantic_entropy_bits=semantic_entropy,
        mean_latency_seconds=2.5,
        median_latency_seconds=median_latency,
        p95_latency_seconds=p95_latency,
        latency_tail_ratio=latency_tail_ratio,
        total_tokens=19000,
        mean_tokens=mean_tokens,
        token_efficiency=token_efficiency,
    )


def test_default_schema_has_unique_features():
    assert len(DEFAULT_FINGERPRINT_SCHEMA.feature_names) == len(
        set(DEFAULT_FINGERPRINT_SCHEMA.feature_names)
    )


def test_default_schema_hash_is_deterministic():
    assert (
        DEFAULT_FINGERPRINT_SCHEMA.schema_sha256
        == DEFAULT_FINGERPRINT_SCHEMA.schema_sha256
    )


def test_schema_rejects_duplicate_feature_names():
    with pytest.raises(ValidationError):
        FingerprintSchema(
            schema_id="bad",
            feature_names=("x", "x"),
            directions={"x": "neutral"},
            bounds={"x": (0.0, 1.0)},
        )


def test_schema_rejects_missing_direction():
    with pytest.raises(ValidationError):
        FingerprintSchema(
            schema_id="bad",
            feature_names=("x",),
            directions={},
            bounds={"x": (0.0, 1.0)},
        )


def test_schema_rejects_invalid_direction():
    with pytest.raises(ValidationError):
        FingerprintSchema(
            schema_id="bad",
            feature_names=("x",),
            directions={"x": "sideways"},
            bounds={"x": (0.0, 1.0)},
        )


def test_bounded_normalize_percent():
    assert bounded_normalize(50, 0, 100) == 0.5


def test_bounded_normalize_clamps():
    assert bounded_normalize(120, 0, 100) == 1.0
    assert bounded_normalize(-1, 0, 100) == 0.0


def test_bounded_normalize_open_upper_bound():
    assert bounded_normalize(3, 0, None) == 0.75


def test_normalizer_orients_lower_is_better():
    normalizer = FingerprintNormalizer(DEFAULT_FINGERPRINT_SCHEMA)
    assert normalizer.normalize_metric("provider_error_rate_pct", 0) == 1.0
    assert normalizer.normalize_metric("provider_error_rate_pct", 100) == 0.0


def test_normalizer_orients_higher_is_better():
    normalizer = FingerprintNormalizer(DEFAULT_FINGERPRINT_SCHEMA)
    assert normalizer.normalize_metric("pass_rate_pct", 90) == 0.9


def test_normalizer_preserves_none():
    normalizer = FingerprintNormalizer(DEFAULT_FINGERPRINT_SCHEMA)
    assert normalizer.normalize_metric("pass_rate_pct", None) is None


def test_normalizer_rejects_unknown_feature():
    normalizer = FingerprintNormalizer(DEFAULT_FINGERPRINT_SCHEMA)
    with pytest.raises(ValidationError):
        normalizer.normalize_metric("unknown", 1)


def test_builder_creates_expected_vector_length():
    fp = FingerprintBuilder().build(metrics())
    assert len(fp.vector) == len(DEFAULT_FINGERPRINT_SCHEMA.feature_names)


def test_builder_preserves_raw_metrics():
    fp = FingerprintBuilder().build(metrics(pass_rate_pct=91.0))
    assert fp.raw_metrics["pass_rate_pct"] == 91.0


def test_builder_preserves_subject_identity():
    fp = FingerprintBuilder().build(
        metrics(provider="deepseek", model="deepseek-test")
    )
    assert fp.provider == "deepseek"
    assert fp.model == "deepseek-test"


def test_builder_preserves_provenance():
    fp = FingerprintBuilder().build(
        metrics(),
        provenance={"run_id": "RUN-001"},
    )
    assert fp.provenance["run_id"] == "RUN-001"


def test_fingerprint_hash_is_deterministic():
    builder = FingerprintBuilder()
    a = builder.build(metrics(), provenance={"run_id": "R1"})
    b = builder.build(metrics(), provenance={"run_id": "R1"})
    assert a.fingerprint_sha256 == b.fingerprint_sha256


def test_fingerprint_hash_changes_when_metric_changes():
    builder = FingerprintBuilder()
    a = builder.build(metrics(pass_rate_pct=90))
    b = builder.build(metrics(pass_rate_pct=80))
    assert a.fingerprint_sha256 != b.fingerprint_sha256


def test_fingerprint_hash_changes_when_provenance_changes():
    builder = FingerprintBuilder()
    a = builder.build(metrics(), provenance={"run_id": "A"})
    b = builder.build(metrics(), provenance={"run_id": "B"})
    assert a.fingerprint_sha256 != b.fingerprint_sha256


def test_verify_identity():
    fp = FingerprintBuilder().build(metrics())
    assert fp.verify_identity()


def test_to_dict_has_schema_version():
    fp = FingerprintBuilder().build(metrics())
    assert fp.to_dict()["schema_version"] == "g6.0"


def test_identical_fingerprints_have_zero_euclidean_distance():
    builder = FingerprintBuilder()
    a = builder.build(metrics(provider="a", model="m1"))
    b = builder.build(metrics(provider="b", model="m2"))
    assert euclidean_distance(a, b) == 0.0


def test_identical_fingerprints_have_zero_manhattan_distance():
    builder = FingerprintBuilder()
    a = builder.build(metrics(provider="a", model="m1"))
    b = builder.build(metrics(provider="b", model="m2"))
    assert manhattan_distance(a, b) == 0.0


def test_identical_nonzero_fingerprints_have_cosine_one():
    builder = FingerprintBuilder()
    a = builder.build(metrics(provider="a", model="m1"))
    b = builder.build(metrics(provider="b", model="m2"))
    assert cosine_similarity(a, b) == pytest.approx(1.0)


def test_comparison_reports_subjects():
    builder = FingerprintBuilder()
    a = builder.build(metrics(provider="openai", model="gpt"))
    b = builder.build(metrics(provider="deepseek", model="ds"))
    result = compare_fingerprints(a, b)
    assert result.provider_a == "openai"
    assert result.provider_b == "deepseek"


def test_comparison_counts_nonmissing_features():
    builder = FingerprintBuilder()
    a = builder.build(metrics())
    b = builder.build(metrics(calibration_error_pct=None))
    result = compare_fingerprints(a, b)
    assert result.comparable_features == len(a.vector) - 1


def test_mismatched_schemas_are_rejected():
    builder_a = FingerprintBuilder()
    custom = FingerprintSchema(
        schema_id="custom",
        feature_names=("pass_rate_pct",),
        directions={"pass_rate_pct": "higher_is_better"},
        bounds={"pass_rate_pct": (0.0, 100.0)},
    )
    builder_b = FingerprintBuilder(custom)
    a = builder_a.build(metrics())
    b = builder_b.build(metrics())
    with pytest.raises(ValidationError):
        compare_fingerprints(a, b)


def test_missing_values_are_excluded_from_distance():
    builder = FingerprintBuilder()
    a = builder.build(metrics(calibration_error_pct=None))
    b = builder.build(metrics(calibration_error_pct=None))
    assert euclidean_distance(a, b) == 0.0


def test_lower_is_better_feature_rewards_smaller_latency():
    builder = FingerprintBuilder()
    fast = builder.build(metrics(median_latency=1.0))
    slow = builder.build(metrics(median_latency=9.0))
    index = DEFAULT_FINGERPRINT_SCHEMA.feature_names.index(
        "median_latency_seconds"
    )
    assert fast.vector[index] > slow.vector[index]


def test_higher_is_better_feature_rewards_pass_rate():
    builder = FingerprintBuilder()
    high = builder.build(metrics(pass_rate_pct=100))
    low = builder.build(metrics(pass_rate_pct=50))
    index = DEFAULT_FINGERPRINT_SCHEMA.feature_names.index("pass_rate_pct")
    assert high.vector[index] > low.vector[index]


def test_fingerprint_feature_order_matches_schema():
    fp = FingerprintBuilder().build(metrics())
    assert tuple(feature.name for feature in fp.features) == (
        DEFAULT_FINGERPRINT_SCHEMA.feature_names
    )


def test_comparison_schema_version():
    builder = FingerprintBuilder()
    a = builder.build(metrics(provider="a", model="m1"))
    b = builder.build(metrics(provider="b", model="m2"))
    assert compare_fingerprints(a, b).to_dict()["schema_version"] == "g6.0"
