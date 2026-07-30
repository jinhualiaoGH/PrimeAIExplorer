from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from core.config import experiment_root


def summarize_scores(config: dict[str, Any]) -> Path:
    root = experiment_root(config)
    source = root / "results" / "response_scores.csv"
    destination = root / "results" / "score_summary.json"

    if not source.exists():
        raise FileNotFoundError(f"Score file not found: {source}")

    with source.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row.get("model", "unknown"), []).append(row)

    summaries: dict[str, Any] = {}
    for model, model_rows in sorted(groups.items()):
        parsed = [r for r in model_rows if r.get("parse_success", "").lower() == "true"]
        exact = [r for r in parsed if r.get("exact_match", "").lower() == "true"]
        structurally_valid = [
            r for r in parsed
            if r.get("structural_validity", "").lower() == "true"
        ]
        absolute_errors = [
            int(r["absolute_error"])
            for r in parsed
            if r.get("absolute_error", "") != ""
        ]

        summaries[model] = {
            "responses": len(model_rows),
            "parsed": len(parsed),
            "exact_matches": len(exact),
            "exact_accuracy": len(exact) / len(parsed) if parsed else None,
            "structurally_valid": len(structurally_valid),
            "structural_validity_rate": (
                len(structurally_valid) / len(parsed) if parsed else None
            ),
            "mean_absolute_error": (
                sum(absolute_errors) / len(absolute_errors)
                if absolute_errors
                else None
            ),
        }

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "experiment_id": config["experiment"]["id"],
                "models": summaries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return destination
