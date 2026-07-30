from __future__ import annotations

import csv
import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

CORE_METRICS = (
    "record_count",
    "accuracy",
    "brier_score",
    "ece",
    "prediction_entropy_bits",
    "distinct_predictions",
    "mean_confidence",
    "mean_signed_error",
    "mean_absolute_error",
)

FINGERPRINT_METRICS = (
    "favorite_prediction",
    "favorite_prediction_share",
    "prediction_entropy_bits",
    "normalized_prediction_entropy",
    "mean_confidence",
    "ece",
    "mean_signed_error",
    "mean_absolute_error",
    "switch_rate",
    "mean_run_length",
    "max_run_length",
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required comparison input not found: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _label(manifest: dict[str, Any], folder: Path, override: str | None) -> str:
    if override:
        return override
    model = str(manifest.get("model") or "unknown-model")
    pilot = str(manifest.get("pilot_id") or folder.name)
    return f"{model} · {pilot}"


def load_analysis(folder: Path, label: str | None = None) -> dict[str, Any]:
    folder = folder.resolve()
    summary = _read_json(folder / "summary.json")
    manifest = _read_json(folder / "manifest.json")
    fingerprint = {
        str(row.get("metric")): row.get("value")
        for row in summary.get("model_fingerprint", [])
        if isinstance(row, dict) and row.get("metric") is not None
    }
    return {
        "folder": str(folder),
        "label": _label(manifest, folder, label),
        "model": manifest.get("model", "unknown-model"),
        "pilot_id": manifest.get("pilot_id", folder.name),
        "experiment_id": manifest.get("experiment_id", "EXP-UNKNOWN"),
        "summary": summary,
        "manifest": manifest,
        "fingerprint": fingerprint,
    }


def discover_analyses(experiment_root: Path, *, exclude: Path | None = None) -> list[Path]:
    """Discover valid analysis folders beneath an experiment directory.

    A valid analysis folder contains both summary.json and manifest.json.
    Comparative-output folders are skipped, as are any paths beneath the
    requested output directory.
    """
    root = experiment_root.resolve()
    excluded = exclude.resolve() if exclude is not None else None
    found: list[Path] = []
    seen: set[Path] = set()
    for summary_path in root.rglob("summary.json"):
        folder = summary_path.parent.resolve()
        if folder in seen:
            continue
        if excluded is not None and (folder == excluded or excluded in folder.parents):
            continue
        lowered = {part.lower() for part in folder.parts}
        if any(part.startswith("comparison") for part in lowered):
            continue
        if not (folder / "manifest.json").is_file():
            continue
        try:
            manifest = _read_json(folder / "manifest.json")
            _read_json(folder / "summary.json")
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        # Analysis manifests contain model/pilot metadata and a summary hash.
        if not any(key in manifest for key in ("model", "pilot_id", "summary_sha256")):
            continue
        seen.add(folder)
        found.append(folder)
    return sorted(found, key=lambda path: str(path).lower())


def select_latest_analyses(folders: list[Path]) -> list[Path]:
    """Keep one auto-discovered analysis per experiment/model/pilot identity.

    Legacy analysis releases for the same response ledger are not independent
    model runs. Prefer the newest manifest timestamp, then the newest folder
    modification time.
    """
    selected: dict[tuple[str, str, str], tuple[tuple[str, float], Path]] = {}
    for folder in folders:
        try:
            manifest = _read_json(folder / "manifest.json")
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        key = (
            str(manifest.get("experiment_id") or "EXP-UNKNOWN").strip().lower(),
            str(manifest.get("model") or "unknown-model").strip().lower().replace("-", " "),
            str(manifest.get("pilot_id") or folder.name).strip().lower(),
        )
        created = str(manifest.get("created_utc") or "")
        score = (created, folder.stat().st_mtime)
        current = selected.get(key)
        if current is None or score > current[0]:
            selected[key] = (score, folder)
    return sorted((item[1] for item in selected.values()), key=lambda path: str(path).lower())


def _number(value: Any) -> float | None:
    """Return a finite float, or None for absent/invalid legacy metrics."""
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _rank(rows: list[dict[str, Any]], key: str, *, lower_is_better: bool) -> None:
    valid = [row for row in rows if _number(row.get(key)) is not None]
    ordered = sorted(
        valid,
        key=lambda row: (_number(row.get(key)), str(row.get("label", ""))),
        reverse=not lower_is_better,
    )
    for row in rows:
        row[f"{key}_rank"] = None
    for rank, row in enumerate(ordered, 1):
        row[f"{key}_rank"] = rank


def _best(rows: list[dict[str, Any]], metric: str, *, lower: bool) -> dict[str, Any] | None:
    valid = [row for row in rows if _number(row.get(metric)) is not None]
    if not valid:
        return None
    chooser = min if lower else max
    return chooser(valid, key=lambda row: (_number(row.get(metric)), str(row.get("label", ""))))


def _mean_available(rows: list[dict[str, Any]], metric: str) -> float | None:
    values = [_number(row.get(metric)) for row in rows]
    present = [value for value in values if value is not None]
    return mean(present) if present else None


def build_comparison(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    if len(analyses) < 2:
        raise ValueError("Comparative observatory requires at least two analysis folders")

    rows: list[dict[str, Any]] = []
    fingerprint_rows: list[dict[str, Any]] = []
    window_rows: list[dict[str, Any]] = []

    for item in analyses:
        summary = item["summary"]
        row: dict[str, Any] = {
            "label": item["label"],
            "model": item["model"],
            "pilot_id": item["pilot_id"],
            "experiment_id": item["experiment_id"],
            "analysis_folder": item["folder"],
        }
        for metric in CORE_METRICS:
            row[metric] = summary.get(metric)
        persistence = summary.get("persistence", {})
        row["switch_rate"] = persistence.get("switch_rate", 0.0)
        row["max_run_length"] = persistence.get("max_run_length", 0)
        row["favorite_prediction"] = item["fingerprint"].get("favorite_prediction")
        row["favorite_prediction_share"] = item["fingerprint"].get("favorite_prediction_share")
        rows.append(row)

        fp_row: dict[str, Any] = {
            "label": item["label"],
            "model": item["model"],
            "pilot_id": item["pilot_id"],
        }
        for metric in FINGERPRINT_METRICS:
            fp_row[metric] = item["fingerprint"].get(metric)
        fingerprint_rows.append(fp_row)

        for window in summary.get("window_observatory", []):
            if not isinstance(window, dict):
                continue
            window_rows.append({"label": item["label"], **window})

    _rank(rows, "accuracy", lower_is_better=False)
    _rank(rows, "brier_score", lower_is_better=True)
    _rank(rows, "ece", lower_is_better=True)
    _rank(rows, "mean_absolute_error", lower_is_better=True)

    rankings: list[dict[str, Any]] = []
    for metric, lower in (
        ("accuracy", False),
        ("brier_score", True),
        ("ece", True),
        ("mean_absolute_error", True),
    ):
        winner = _best(rows, metric, lower=lower)
        if winner is None:
            continue
        rankings.append({
            "metric": metric,
            "best_label": winner["label"],
            "best_value": _number(winner.get(metric)),
            "direction": "lower" if lower else "higher",
        })

    return {
        "schema_version": "0.7.3",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_count": len(analyses),
        "experiment_ids": sorted({str(item["experiment_id"]) for item in analyses}),
        "models": sorted({str(item["model"]) for item in analyses}),
        "pilots": sorted({str(item["pilot_id"]) for item in analyses}),
        "comparison_rows": rows,
        "fingerprint_matrix": fingerprint_rows,
        "window_comparison": window_rows,
        "rankings": rankings,
        "aggregate": {
            "mean_accuracy": _mean_available(rows, "accuracy"),
            "mean_brier_score": _mean_available(rows, "brier_score"),
            "mean_ece": _mean_available(rows, "ece"),
            "mean_absolute_error": _mean_available(rows, "mean_absolute_error"),
        },
        "sources": [
            {
                "label": item["label"],
                "folder": item["folder"],
                "summary_sha256": item["manifest"].get("summary_sha256"),
            }
            for item in analyses
        ],
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _finite_number(value: Any) -> float | None:
    """Return a finite float, or None for missing/legacy values."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _fmt_number(value: Any, spec: str, missing: str = "—") -> str:
    number = _finite_number(value)
    return missing if number is None else format(number, spec)


def _fmt_percent(value: Any, missing: str = "—") -> str:
    return _fmt_number(value, ".2%", missing)


def markdown_report(comparison: dict[str, Any]) -> str:
    lines = [
        "# PrimeAIExplorer v0.7.3 Comparative Observatory",
        "",
        f"Analyses compared: **{comparison['analysis_count']}**",
        "",
        "## Model and pilot comparison",
        "",
        "| Label | Records | Accuracy | Brier | ECE | Mean |error| | Switch rate | Favorite |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparison["comparison_rows"]:
        lines.append(
            f"| {row['label']} | {row.get('record_count', 0)} | {_fmt_percent(row.get('accuracy'))} | "
            f"{_fmt_number(row.get('brier_score'), '.4f')} | {_fmt_number(row.get('ece'), '.4f')} | "
            f"{_fmt_number(row.get('mean_absolute_error'), '.2f')} | {_fmt_percent(row.get('switch_rate'))} | "
            f"{row.get('favorite_prediction', '') if row.get('favorite_prediction') is not None else '—'} |"
        )
    lines.extend(["", "## Best observed values", ""])
    for row in comparison["rankings"]:
        lines.append(
            f"- **{row['metric']}**: {row['best_label']} ({float(row['best_value']):.6g}; {row['direction']} is better)"
        )
    return "\n".join(lines) + "\n"


def _pct(value: Any) -> str:
    return _fmt_percent(value)


def html_report(comparison: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(row['label']))}</td>"
        f"<td>{row.get('record_count', 0)}</td>"
        f"<td>{_pct(row.get('accuracy'))}</td>"
        f"<td>{_fmt_number(row.get('brier_score'), '.4f')}</td>"
        f"<td>{_fmt_number(row.get('ece'), '.4f')}</td>"
        f"<td>{_fmt_number(row.get('prediction_entropy_bits'), '.3f')}</td>"
        f"<td>{_fmt_number(row.get('mean_absolute_error'), '.2f')}</td>"
        f"<td>{_fmt_number(row.get('mean_signed_error'), '+.2f')}</td>"
        f"<td>{_pct(row.get('switch_rate'))}</td>"
        f"<td>{row.get('favorite_prediction', '') if row.get('favorite_prediction') is not None else '—'}</td>"
        "</tr>"
        for row in comparison["comparison_rows"]
    )
    ranking_cards = "".join(
        f"<div class='card'><div>{html.escape(row['metric'])}</div><div class='big'>{html.escape(str(row['best_label']))}</div><div>{float(row['best_value']):.4g}</div></div>"
        for row in comparison["rankings"]
    )
    fingerprint_headers = "".join(f"<th>{html.escape(metric)}</th>" for metric in FINGERPRINT_METRICS)
    fingerprint_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(row['label']))}</td>"
        + "".join(f"<td>{'' if row.get(metric) is None else row.get(metric)}</td>" for metric in FINGERPRINT_METRICS)
        + "</tr>"
        for row in comparison["fingerprint_matrix"]
    )
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>PrimeAIExplorer v0.7.3</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f8;color:#17202a}}header{{background:#152536;color:#fff;padding:34px 5%}}main{{max-width:1400px;margin:auto;padding:24px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}}.card,.panel{{background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 9px #0001}}.big{{font-size:20px;font-weight:700;margin:8px 0}}table{{border-collapse:collapse;width:100%;background:#fff;margin:12px 0 28px}}th,td{{padding:9px;border-bottom:1px solid #ddd;text-align:center;white-space:nowrap}}th{{background:#e9eef3;position:sticky;top:0}}.scroll{{overflow:auto}}h2{{margin-top:34px}}.muted{{color:#64748b}}
</style></head><body><header><h1>PrimeAIExplorer v0.7.3</h1><p>Comparative Observatory · {comparison['analysis_count']} analyses</p></header><main>
<h2>Best observed values</h2><div class='cards'>{ranking_cards}</div>
<h2>Model and pilot comparison</h2><div class='panel scroll'><table><tr><th>Label</th><th>N</th><th>Accuracy</th><th>Brier</th><th>ECE</th><th>Entropy</th><th>Mean |error|</th><th>Signed error</th><th>Switch rate</th><th>Favorite</th></tr>{rows}</table></div>
<h2>Model fingerprint matrix</h2><div class='panel scroll'><table><tr><th>Label</th>{fingerprint_headers}</tr>{fingerprint_rows}</table></div>
<p class='muted'>Comparisons are descriptive. Interpret rankings cautiously when pilots have different sample sizes, datasets, or collection protocols.</p>
</main></body></html>"""
