from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from kernel.exceptions import ValidationError

from .observatory import BehavioralObservatorySnapshot


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def _flatten_drift(snapshot: BehavioralObservatorySnapshot) -> list[dict[str, Any]]:
    rows = []
    for campaign in snapshot.drift_reports:
        for report in campaign.reports:
            for feature in report.features:
                rows.append(
                    {
                        "baseline_id": campaign.baseline_id,
                        "provider": report.provider,
                        "baseline_model": report.baseline_model,
                        "current_model": report.current_model,
                        "classification": report.classification,
                        "aggregate_drift_score": report.aggregate_drift_score,
                        "feature": feature.name,
                        "baseline_value": feature.baseline_value,
                        "current_value": feature.current_value,
                        "delta": feature.delta,
                        "absolute_delta": feature.absolute_delta,
                        "direction": feature.direction,
                        "interpretation": feature.interpretation,
                    }
                )
    return rows


def _fingerprint_rows(snapshot: BehavioralObservatorySnapshot) -> list[dict[str, Any]]:
    rows = []
    for fingerprint in snapshot.fingerprints:
        for feature in fingerprint.features:
            rows.append(
                {
                    "provider": fingerprint.provider,
                    "model": fingerprint.model,
                    "fingerprint_sha256": fingerprint.fingerprint_sha256,
                    "feature": feature.name,
                    "raw_value": feature.raw_value,
                    "normalized_value": feature.normalized_value,
                    "direction": feature.direction,
                }
            )
    return rows


def _html_document(snapshot: BehavioralObservatorySnapshot) -> str:
    providers = snapshot.metrics_report.provider_metrics
    matrix = snapshot.comparison_matrix

    provider_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row.provider)}</td>"
        f"<td>{html.escape(row.model)}</td>"
        f"<td>{row.observations}</td>"
        f"<td>{'' if row.pass_rate_pct is None else f'{row.pass_rate_pct:.2f}'}</td>"
        f"<td>{'' if row.provider_error_rate_pct is None else f'{row.provider_error_rate_pct:.2f}'}</td>"
        f"<td>{'' if row.mean_case_semantic_consistency_pct is None else f'{row.mean_case_semantic_consistency_pct:.2f}'}</td>"
        f"<td>{'' if row.median_latency_seconds is None else f'{row.median_latency_seconds:.4f}'}</td>"
        "</tr>"
        for row in providers
    ) or '<tr><td colspan="7">No provider metrics.</td></tr>'

    matrix_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(entry.row_subject)}</td>"
        f"<td>{html.escape(entry.column_subject)}</td>"
        f"<td>{entry.comparable_features}</td>"
        f"<td>{'' if entry.euclidean_distance is None else f'{entry.euclidean_distance:.6f}'}</td>"
        f"<td>{'' if entry.cosine_similarity is None else f'{entry.cosine_similarity:.6f}'}</td>"
        "</tr>"
        for entry in matrix.entries
    ) or '<tr><td colspan="5">No fingerprint comparisons.</td></tr>'

    drift_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(campaign.baseline_id)}</td>"
        f"<td>{html.escape(report.provider)}</td>"
        f"<td>{html.escape(report.baseline_model)}</td>"
        f"<td>{html.escape(report.current_model)}</td>"
        f"<td>{html.escape(report.classification)}</td>"
        f"<td>{'' if report.aggregate_drift_score is None else f'{report.aggregate_drift_score:.6f}'}</td>"
        "</tr>"
        for campaign in snapshot.drift_reports
        for report in campaign.reports
    ) or '<tr><td colspan="6">No drift reports.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PrimeAIExplorer Behavioral Observatory</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.4; }}
h1, h2 {{ margin-bottom: .4rem; }}
.small {{ color: #555; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
th, td {{ border: 1px solid #bbb; padding: .45rem .55rem; text-align: left; }}
th {{ background: #f3f3f3; }}
code {{ overflow-wrap: anywhere; }}
</style>
</head>
<body>
<h1>PrimeAIExplorer Behavioral Observatory</h1>
<p class="small">Snapshot: {html.escape(snapshot.snapshot_id)}<br>
SHA-256: <code>{snapshot.snapshot_sha256}</code></p>

<h2>Provider / Model Summary</h2>
<table>
<thead><tr>
<th>Provider</th><th>Model</th><th>Observations</th><th>Pass %</th>
<th>Provider Error %</th><th>Semantic Consistency %</th><th>Median Latency s</th>
</tr></thead>
<tbody>
{provider_rows}
</tbody>
</table>

<h2>Fingerprint Comparison Matrix</h2>
<table>
<thead><tr>
<th>Row</th><th>Column</th><th>Comparable Features</th>
<th>Euclidean Distance</th><th>Cosine Similarity</th>
</tr></thead>
<tbody>
{matrix_rows}
</tbody>
</table>

<h2>Behavioral Drift</h2>
<table>
<thead><tr>
<th>Baseline</th><th>Provider</th><th>Baseline Model</th>
<th>Current Model</th><th>Classification</th><th>RMS Drift</th>
</tr></thead>
<tbody>
{drift_rows}
</tbody>
</table>

<p class="small">
G8 is a presentation layer. Scientific semantics are inherited from frozen G1-G7 contracts.
</p>
</body>
</html>
"""


def export_observatory_bundle(
    snapshot: BehavioralObservatorySnapshot,
    output_dir: str | Path,
) -> tuple[Path, ...]:
    if not isinstance(snapshot, BehavioralObservatorySnapshot):
        raise ValidationError(
            "snapshot must be BehavioralObservatorySnapshot."
        )

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    snapshot_json = root / "snapshot.json"
    provider_csv = root / "provider_metrics.csv"
    case_csv = root / "case_metrics.csv"
    comparison_csv = root / "comparison_matrix.csv"
    fingerprint_csv = root / "fingerprint_features.csv"
    drift_csv = root / "drift_features.csv"
    index_html = root / "index.html"

    _write_json(snapshot_json, snapshot.to_dict())

    provider_rows = [
        row.to_dict()
        for row in snapshot.metrics_report.provider_metrics
    ]
    provider_fields = sorted(
        {
            key
            for row in provider_rows
            for key in row
            if key != "schema_version"
        }
    )
    _write_csv(
        provider_csv,
        provider_fields,
        (
            {key: value for key, value in row.items() if key != "schema_version"}
            for row in provider_rows
        ),
    )

    case_rows = [
        row.to_dict()
        for row in snapshot.metrics_report.case_metrics
    ]
    case_fields = sorted(
        {
            key
            for row in case_rows
            for key in row
            if key != "schema_version"
        }
    )
    _write_csv(
        case_csv,
        case_fields,
        (
            {key: value for key, value in row.items() if key != "schema_version"}
            for row in case_rows
        ),
    )

    comparison_rows = [
        row.to_dict()
        for row in snapshot.comparison_matrix.entries
    ]
    comparison_fields = [
        "row_subject",
        "column_subject",
        "comparable_features",
        "euclidean_distance",
        "manhattan_distance",
        "cosine_similarity",
    ]
    _write_csv(comparison_csv, comparison_fields, comparison_rows)

    fingerprint_rows = _fingerprint_rows(snapshot)
    fingerprint_fields = [
        "provider",
        "model",
        "fingerprint_sha256",
        "feature",
        "raw_value",
        "normalized_value",
        "direction",
    ]
    _write_csv(fingerprint_csv, fingerprint_fields, fingerprint_rows)

    drift_rows = _flatten_drift(snapshot)
    drift_fields = [
        "baseline_id",
        "provider",
        "baseline_model",
        "current_model",
        "classification",
        "aggregate_drift_score",
        "feature",
        "baseline_value",
        "current_value",
        "delta",
        "absolute_delta",
        "direction",
        "interpretation",
    ]
    _write_csv(drift_csv, drift_fields, drift_rows)

    index_html.write_text(
        _html_document(snapshot),
        encoding="utf-8",
    )

    return (
        snapshot_json,
        provider_csv,
        case_csv,
        comparison_csv,
        fingerprint_csv,
        drift_csv,
        index_html,
    )
