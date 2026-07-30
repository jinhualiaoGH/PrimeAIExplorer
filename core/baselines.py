from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import experiment_root
from core.io import read_json, write_json
from core.plugin import SequencePlugin


def _case_to_window(plugin: SequencePlugin, case: dict[str, Any]):
    return plugin.make_window(
        endpoint_index_1_based=int(case["endpoint_index_1_based"]),
        window_size=int(case["window_size"]),
        representation=str(case["representation"]),
    )


def generate_baseline_responses(
    config: dict[str, Any],
    plugin: SequencePlugin,
) -> dict[str, int]:
    root = experiment_root(config)
    public_dir = root / "cases" / "public"
    response_root = root / "responses"
    counts: dict[str, int] = {}

    for case_path in sorted(public_dir.glob("CASE-*.json")):
        case = read_json(case_path)
        window = _case_to_window(plugin, case)
        predictions = plugin.baseline_predictions(window)

        for baseline_id, prediction in predictions.items():
            output = response_root / f"baseline_{baseline_id}" / case_path.name
            write_json(
                output,
                {
                    "prediction": int(prediction),
                    "confidence": 0,
                    "explanation": (
                        f"Deterministic baseline: {baseline_id}. "
                        "Confidence is fixed at zero because this is not "
                        "a calibrated probabilistic forecast."
                    ),
                },
            )
            counts[baseline_id] = counts.get(baseline_id, 0) + 1

    manifest = {
        "experiment_id": config["experiment"]["id"],
        "sequence_plugin": plugin.plugin_name,
        "baseline_counts": counts,
    }
    write_json(root / "responses" / "baseline_manifest.json", manifest)
    return counts
