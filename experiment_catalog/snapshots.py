"""Construct immutable catalog snapshots from PrimeAIExplorer artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .canonical import record_id_from_snapshot, snapshot_sha256
from .loading import (
    count_jsonl_records,
    discover_experiment_files,
    load_json_object,
    load_optional_json_object,
)
from .models import CatalogRecord


def build_catalog_record(
    experiment_directory: str | Path,
    *,
    dataset_manifest: str | Path | None = None,
    analysis_json: str | Path | None = None,
    report_manifest: str | Path | None = None,
) -> CatalogRecord:
    files = discover_experiment_files(experiment_directory)
    experiment = load_json_object(files["experiment"])
    state = load_json_object(files["state"])
    dataset = load_optional_json_object(dataset_manifest)
    analysis = load_optional_json_object(analysis_json)
    report = load_optional_json_object(report_manifest)

    experiment_id = str(
        state.get("experiment_id")
        or experiment.get("experiment_id")
        or Path(experiment_directory).name
    )

    snapshot: dict[str, Any] = {
        "experiment": experiment,
        "state": state,
        "dataset_manifest": dataset,
        "analysis": analysis,
        "report_manifest": report,
        "responses_record_count": count_jsonl_records(files["responses"]),
    }

    digest = snapshot_sha256(snapshot)

    model_parameters = experiment.get("model_parameters", {})
    if not isinstance(model_parameters, dict):
        model_parameters = {}

    provider = _optional_string(
        experiment.get("model_provider")
        or model_parameters.get("provider")
    )
    model = _optional_string(
        experiment.get("model_name")
        or model_parameters.get("model")
    )

    dataset_id = None
    sequence_type = _optional_string(
        experiment.get("sequence_plugin")
        or experiment.get("sequence_type")
    )
    if dataset is not None:
        dataset_id = _optional_string(dataset.get("dataset_id"))
        sequence_type = (
            _optional_string(dataset.get("sequence_type"))
            or sequence_type
        )

    report_path = None
    if report is not None:
        report_path = _optional_string(
            report.get("report_path")
            or report.get("output_directory")
        )

    return CatalogRecord(
        record_id=record_id_from_snapshot(snapshot),
        experiment_id=experiment_id,
        dataset_id=dataset_id,
        name=str(experiment.get("name", experiment_id)),
        status=str(state.get("status", "unknown")),
        provider=provider,
        model=model,
        sequence_type=sequence_type,
        case_count=_optional_int(
            state.get("case_count")
            or experiment.get("case_count")
        ),
        completed_case_count=_optional_int(
            state.get("completed_case_count")
        ),
        failed_case_count=_optional_int(
            state.get("failed_case_count")
        ),
        accuracy=_optional_float(
            analysis.get("accuracy") if analysis else None
        ),
        mean_absolute_error=_optional_float(
            analysis.get("mean_absolute_error") if analysis else None
        ),
        report_path=report_path,
        created_at_utc=_optional_string(state.get("created_at_utc")),
        started_at_utc=_optional_string(state.get("started_at_utc")),
        completed_at_utc=_optional_string(state.get("completed_at_utc")),
        snapshot_sha256=digest,
        snapshot=snapshot,
    )


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None
