from __future__ import annotations

import json

from experiment_catalog import (
    ExperimentCatalog,
    SearchQuery,
    build_catalog_record,
)


def make_experiment(tmp_path, *, accuracy=0.75, status="completed"):
    experiment = tmp_path / "EXP-TEST"
    (experiment / "results").mkdir(parents=True)

    (experiment / "experiment.json").write_text(
        json.dumps(
            {
                "experiment_id": "EXP-TEST",
                "name": "Fixture Experiment",
                "case_count": 2,
                "model_provider": "manual",
                "model_name": "fixture-model",
                "sequence_plugin": "prime-gap",
            }
        ),
        encoding="utf-8-sig",
    )
    (experiment / "state.json").write_text(
        json.dumps(
            {
                "experiment_id": "EXP-TEST",
                "status": status,
                "case_count": 2,
                "completed_case_count": 2 if status == "completed" else 1,
                "failed_case_count": 0,
                "created_at_utc": "2026-08-01T12:00:00Z",
                "started_at_utc": "2026-08-01T12:01:00Z",
                "completed_at_utc": (
                    "2026-08-01T12:02:00Z"
                    if status == "completed"
                    else None
                ),
            }
        ),
        encoding="utf-8",
    )
    (experiment / "results" / "responses.jsonl").write_text(
        '{"case_id":"A"}\n{"case_id":"B"}\n',
        encoding="utf-8",
    )

    dataset = tmp_path / "dataset_manifest.json"
    dataset.write_text(
        json.dumps(
            {
                "dataset_id": "DS-1234567890ABCDEF",
                "sequence_type": "prime-gap",
            }
        ),
        encoding="utf-8",
    )

    analysis = tmp_path / "analysis.json"
    analysis.write_text(
        json.dumps(
            {
                "accuracy": accuracy,
                "mean_absolute_error": 1.25,
            }
        ),
        encoding="utf-8",
    )

    report = tmp_path / "report_manifest.json"
    report.write_text(
        json.dumps(
            {
                "report_path": "reports/EXP-TEST/report.html",
            }
        ),
        encoding="utf-8",
    )

    return experiment, dataset, analysis, report


def test_snapshot_record_is_deterministic(tmp_path):
    experiment, dataset, analysis, report = make_experiment(tmp_path)

    first = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )
    second = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )

    assert first.record_id == second.record_id
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.dataset_id == "DS-1234567890ABCDEF"


def test_registration_is_idempotent(tmp_path):
    experiment, dataset, analysis, report = make_experiment(tmp_path)
    record = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )
    catalog = ExperimentCatalog(tmp_path / "catalog.sqlite3")

    assert catalog.register(record) is True
    assert catalog.register(record) is False
    assert catalog.count() == 1


def test_search_filters_by_provider_status_and_accuracy(tmp_path):
    experiment, dataset, analysis, report = make_experiment(tmp_path)
    record = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )
    catalog = ExperimentCatalog(tmp_path / "catalog.sqlite3")
    catalog.register(record)

    matches = catalog.search(
        SearchQuery(
            provider="manual",
            status="completed",
            min_accuracy=0.7,
        )
    )
    misses = catalog.search(
        SearchQuery(
            provider="openai",
        )
    )

    assert [item.record_id for item in matches] == [record.record_id]
    assert misses == []


def test_history_keeps_multiple_snapshots(tmp_path):
    experiment, dataset, analysis, report = make_experiment(
        tmp_path,
        accuracy=0.5,
        status="running",
    )
    catalog = ExperimentCatalog(tmp_path / "catalog.sqlite3")

    first = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )
    catalog.register(first)

    state = json.loads((experiment / "state.json").read_text())
    state["status"] = "completed"
    state["completed_case_count"] = 2
    state["completed_at_utc"] = "2026-08-01T12:05:00Z"
    (experiment / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    second = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )
    catalog.register(second)

    history = catalog.history("EXP-TEST")

    assert len(history) == 2
    assert history[0].record_id != history[1].record_id


def test_latest_returns_completed_snapshot(tmp_path):
    experiment, dataset, analysis, report = make_experiment(
        tmp_path,
        status="running",
    )
    catalog = ExperimentCatalog(tmp_path / "catalog.sqlite3")
    running = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )
    catalog.register(running)

    state = json.loads((experiment / "state.json").read_text())
    state["status"] = "completed"
    state["completed_at_utc"] = "2026-08-01T12:10:00Z"
    (experiment / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )
    completed = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )
    catalog.register(completed)

    latest = catalog.latest_for_experiment("EXP-TEST")

    assert latest is not None
    assert latest.status == "completed"


def test_export_jsonl_is_deterministic(tmp_path):
    experiment, dataset, analysis, report = make_experiment(tmp_path)
    record = build_catalog_record(
        experiment,
        dataset_manifest=dataset,
        analysis_json=analysis,
        report_manifest=report,
    )
    catalog = ExperimentCatalog(tmp_path / "catalog.sqlite3")
    catalog.register(record)

    first = catalog.export_jsonl(tmp_path / "first.jsonl")
    second = catalog.export_jsonl(tmp_path / "second.jsonl")

    assert first.read_bytes() == second.read_bytes()
