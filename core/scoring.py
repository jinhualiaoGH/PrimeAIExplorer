from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import experiment_root
from core.io import read_json, write_csv
from core.plugin import SequencePlugin


def parse_response(path: Path) -> tuple[dict[str, Any] | None, str]:
    try:
        value = read_json(path)
    except Exception as exc:
        return None, f"json_error: {exc}"

    if not isinstance(value, dict):
        return None, "response_not_object"
    if "prediction" not in value:
        return None, "missing_prediction"
    if isinstance(value["prediction"], bool) or not isinstance(value["prediction"], int):
        return None, "prediction_not_integer"

    confidence = value.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, int):
            return None, "confidence_not_integer"
        if not 0 <= confidence <= 100:
            return None, "confidence_out_of_range"

    return value, ""


def score_responses(config: dict[str, Any], plugin: SequencePlugin) -> Path:
    root = experiment_root(config)
    answer_dir = root / "cases" / "answer_keys"
    response_paths = sorted((root / "responses").glob("**/CASE-*.json"))
    rows: list[dict[str, Any]] = []

    for response_path in response_paths:
        case_id = response_path.stem
        answer_path = answer_dir / f"{case_id}.answer.json"
        model = response_path.parent.name

        if not answer_path.exists():
            rows.append({
                "case_id": case_id,
                "model": model,
                "parse_success": False,
                "error": "answer_key_not_found",
            })
            continue

        answer = read_json(answer_path)
        response, error = parse_response(response_path)
        if response is None:
            rows.append({
                "case_id": case_id,
                "model": model,
                "parse_success": False,
                "error": error,
            })
            continue

        prediction = int(response["prediction"])
        target = int(answer["target_value"])
        current = answer.get("current_value")
        absolute_error = abs(prediction - target)

        row = {
            "case_id": case_id,
            "model": model,
            "parse_success": True,
            "error": "",
            "prediction": prediction,
            "target": target,
            "exact_match": prediction == target,
            "absolute_error": absolute_error,
            "relative_error": absolute_error / abs(target) if target != 0 else None,
            "confidence": response.get("confidence"),
            "explanation": response.get("explanation", ""),
            "structural_validity": plugin.structural_validity(prediction),
        }

        if current is not None:
            row["predicted_gap"] = prediction - int(current)
            row["target_gap"] = target - int(current)
            row["absolute_gap_error"] = abs(row["predicted_gap"] - row["target_gap"])

        rows.append(row)

    output = root / "results" / "response_scores.csv"
    write_csv(output, rows)
    return output
