import csv
import json

import pytest

from behavioral_evaluation import (
    BehavioralEvaluationRecord,
    EvaluationDisposition,
    FingerprintBaseline,
    FingerprintBaselineRegistry,
    FingerprintBuilder,
    ProviderExecutionStatus,
    build_behavioral_metrics_report,
    build_observatory_snapshot,
    compare_to_baseline,
    export_observatory_bundle,
)
from kernel.exceptions import ValidationError


def record(
    *,
    observation_id,
    provider,
    model,
    case_id,
    trial_index,
    semantic,
    surface,
    passed=True,
    score=100.0,
    confidence=90,
    latency=1.0,
    tokens=100,
):
    return BehavioralEvaluationRecord(
        observation_id=observation_id,
        contract_id="prime-gap.numeric-exact",
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
        total_tokens=tokens,
        surface_answer=surface,
        semantic_answer=semantic,
    )


def records():
    return (
        record(
            observation_id="OBS-" + "A" * 24,
            provider="openai",
            model="gpt-a",
            case_id="CASE-1",
            trial_index=1,
            semantic=4,
            surface="4",
        ),
        record(
            observation_id="OBS-" + "B" * 24,
            provider="openai",
            model="gpt-a",
            case_id="CASE-1",
            trial_index=2,
            semantic=4,
            surface="answer 4",
        ),
        record(
            observation_id="OBS-" + "C" * 24,
            provider="deepseek",
            model="ds-a",
            case_id="CASE-1",
            trial_index=1,
            semantic=4,
            surface="4",
        ),
        record(
            observation_id="OBS-" + "D" * 24,
            provider="deepseek",
            model="ds-a",
            case_id="CASE-1",
            trial_index=2,
            semantic=6,
            surface="6",
            passed=False,
            score=0.0,
        ),
    )


def artifacts():
    report = build_behavioral_metrics_report(records())
    fingerprints = tuple(
        FingerprintBuilder().build(
            provider_metrics,
            provenance={"campaign": "G8-TEST"},
        )
        for provider_metrics in report.provider_metrics
    )
    baseline = FingerprintBaseline("baseline", fingerprints[0])
    registry = FingerprintBaselineRegistry((baseline,))
    drift = compare_to_baseline(
        registry,
        "baseline",
        fingerprints,
    )
    return report, fingerprints, (drift,)


def snapshot():
    report, fingerprints, drift = artifacts()
    return build_observatory_snapshot(
        snapshot_id="OBSERVATORY-001",
        metrics_report=report,
        fingerprints=fingerprints,
        drift_reports=drift,
        metadata={"campaign": "G8-TEST"},
    )


def test_snapshot_has_schema_version():
    assert snapshot().to_dict()["schema_version"] == "g8.0"


def test_snapshot_id_is_preserved():
    assert snapshot().snapshot_id == "OBSERVATORY-001"


def test_snapshot_fingerprints_are_deterministically_sorted():
    subjects = tuple(
        f"{item.provider}/{item.model}"
        for item in snapshot().fingerprints
    )
    assert subjects == tuple(sorted(subjects))


def test_snapshot_drift_reports_are_sorted_by_baseline():
    snap = snapshot()
    assert [item.baseline_id for item in snap.drift_reports] == ["baseline"]


def test_snapshot_matrix_matches_fingerprint_subjects():
    snap = snapshot()
    subjects = tuple(
        sorted(f"{item.provider}/{item.model}" for item in snap.fingerprints)
    )
    assert snap.comparison_matrix.subjects == subjects


def test_snapshot_hash_is_deterministic():
    assert snapshot().snapshot_sha256 == snapshot().snapshot_sha256


def test_snapshot_hash_changes_with_metadata():
    report, fingerprints, drift = artifacts()
    a = build_observatory_snapshot(
        snapshot_id="S",
        metrics_report=report,
        fingerprints=fingerprints,
        drift_reports=drift,
        metadata={"x": 1},
    )
    b = build_observatory_snapshot(
        snapshot_id="S",
        metrics_report=report,
        fingerprints=fingerprints,
        drift_reports=drift,
        metadata={"x": 2},
    )
    assert a.snapshot_sha256 != b.snapshot_sha256


def test_snapshot_rejects_empty_id():
    report, fingerprints, drift = artifacts()
    with pytest.raises(ValidationError):
        build_observatory_snapshot(
            snapshot_id="",
            metrics_report=report,
            fingerprints=fingerprints,
            drift_reports=drift,
        )


def test_export_bundle_creates_expected_files(tmp_path):
    paths = export_observatory_bundle(snapshot(), tmp_path)
    assert {path.name for path in paths} == {
        "snapshot.json",
        "provider_metrics.csv",
        "case_metrics.csv",
        "comparison_matrix.csv",
        "fingerprint_features.csv",
        "drift_features.csv",
        "index.html",
    }


def test_snapshot_json_round_trips(tmp_path):
    export_observatory_bundle(snapshot(), tmp_path)
    data = json.loads((tmp_path / "snapshot.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "g8.0"
    assert data["snapshot_id"] == "OBSERVATORY-001"


def test_provider_csv_has_two_rows(tmp_path):
    export_observatory_bundle(snapshot(), tmp_path)
    with (tmp_path / "provider_metrics.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2


def test_case_csv_has_two_rows(tmp_path):
    export_observatory_bundle(snapshot(), tmp_path)
    with (tmp_path / "case_metrics.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2


def test_comparison_csv_has_n_squared_rows(tmp_path):
    export_observatory_bundle(snapshot(), tmp_path)
    with (tmp_path / "comparison_matrix.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4


def test_fingerprint_csv_contains_all_features(tmp_path):
    snap = snapshot()
    export_observatory_bundle(snap, tmp_path)
    with (tmp_path / "fingerprint_features.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    expected = sum(len(fp.features) for fp in snap.fingerprints)
    assert len(rows) == expected


def test_drift_csv_contains_feature_rows(tmp_path):
    snap = snapshot()
    export_observatory_bundle(snap, tmp_path)
    with (tmp_path / "drift_features.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    expected = sum(
        len(report.features)
        for campaign in snap.drift_reports
        for report in campaign.reports
    )
    assert len(rows) == expected


def test_html_contains_observatory_title(tmp_path):
    export_observatory_bundle(snapshot(), tmp_path)
    text = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "PrimeAIExplorer Behavioral Observatory" in text


def test_html_contains_snapshot_id(tmp_path):
    export_observatory_bundle(snapshot(), tmp_path)
    text = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "OBSERVATORY-001" in text


def test_html_contains_provider_names(tmp_path):
    export_observatory_bundle(snapshot(), tmp_path)
    text = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "openai" in text
    assert "deepseek" in text


def test_html_contains_drift_section(tmp_path):
    export_observatory_bundle(snapshot(), tmp_path)
    text = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Behavioral Drift" in text


def test_export_is_deterministic_for_json(tmp_path):
    snap = snapshot()
    first = tmp_path / "first"
    second = tmp_path / "second"
    export_observatory_bundle(snap, first)
    export_observatory_bundle(snap, second)
    assert (
        (first / "snapshot.json").read_bytes()
        == (second / "snapshot.json").read_bytes()
    )


def test_export_is_deterministic_for_html(tmp_path):
    snap = snapshot()
    first = tmp_path / "first"
    second = tmp_path / "second"
    export_observatory_bundle(snap, first)
    export_observatory_bundle(snap, second)
    assert (
        (first / "index.html").read_bytes()
        == (second / "index.html").read_bytes()
    )


def test_export_rejects_non_snapshot(tmp_path):
    with pytest.raises(ValidationError):
        export_observatory_bundle({}, tmp_path)


def test_empty_observatory_is_valid(tmp_path):
    report = build_behavioral_metrics_report(())
    snap = build_observatory_snapshot(
        snapshot_id="EMPTY",
        metrics_report=report,
        fingerprints=(),
    )
    paths = export_observatory_bundle(snap, tmp_path)
    assert snap.comparison_matrix.subjects == ()
    assert len(paths) == 7


def test_empty_csv_files_still_have_export_paths(tmp_path):
    report = build_behavioral_metrics_report(())
    snap = build_observatory_snapshot(
        snapshot_id="EMPTY",
        metrics_report=report,
        fingerprints=(),
    )
    export_observatory_bundle(snap, tmp_path)
    assert (tmp_path / "provider_metrics.csv").exists()
    assert (tmp_path / "case_metrics.csv").exists()


def test_snapshot_metadata_is_preserved():
    assert snapshot().metadata["campaign"] == "G8-TEST"


def test_snapshot_contains_comparison_matrix():
    assert len(snapshot().comparison_matrix.entries) == 4


def test_snapshot_contains_fingerprints():
    assert len(snapshot().fingerprints) == 2


def test_snapshot_contains_metrics_report():
    assert len(snapshot().metrics_report.provider_metrics) == 2


def test_snapshot_contains_drift_report():
    assert len(snapshot().drift_reports) == 1


def test_snapshot_to_dict_contains_all_sections():
    data = snapshot().to_dict()
    assert set(data) == {
        "schema_version",
        "snapshot_id",
        "metrics_report",
        "fingerprints",
        "comparison_matrix",
        "drift_reports",
        "metadata",
    }
