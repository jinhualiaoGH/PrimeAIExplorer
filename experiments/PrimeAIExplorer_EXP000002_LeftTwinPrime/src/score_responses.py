from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from common import experiment_root, load_config


def parse_response(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as f:
            value = json.load(f)
    except Exception as exc:
        return None, f"json_error: {exc}"

    if not isinstance(value, dict):
        return None, "response_not_object"
    if "prediction" not in value:
        return None, "missing_prediction"

    prediction = value["prediction"]
    confidence = value.get("confidence")

    if isinstance(prediction, bool) or not isinstance(prediction, int):
        return None, "prediction_not_integer"
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, int):
            return None, "confidence_not_integer"
        if not 0 <= confidence <= 100:
            return None, "confidence_out_of_range"

    return value, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Score collected LTP model responses.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    root = experiment_root(config)
    answer_dir = root / "cases" / "answer_keys"
    results_dir = root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    response_paths = sorted(root.glob(config["response_glob"]))
    rows = []

    for response_path in response_paths:
        case_id = response_path.stem
        answer_path = answer_dir / f"{case_id}.answer.json"
        if not answer_path.exists():
            rows.append(
                {
                    "case_id": case_id,
                    "response_path": str(response_path),
                    "parse_success": False,
                    "error": "answer_key_not_found",
                }
            )
            continue

        with answer_path.open("r", encoding="utf-8") as f:
            answer = json.load(f)

        response, error = parse_response(response_path)
        if error:
            rows.append(
                {
                    "case_id": case_id,
                    "response_path": str(response_path),
                    "parse_success": False,
                    "error": error,
                }
            )
            continue

        prediction = int(response["prediction"])
        target = int(answer["target_left_twin_prime"])
        current = int(answer["current_left_twin_prime"])
        target_gap = int(answer["target_gap"])
        predicted_gap = prediction - current
        absolute_error = abs(prediction - target)

        rows.append(
            {
                "case_id": case_id,
                "response_path": str(response_path),
                "parse_success": True,
                "error": "",
                "prediction": prediction,
                "target": target,
                "exact_value_match": prediction == target,
                "absolute_error": absolute_error,
                "relative_error": absolute_error / target,
                "predicted_gap": predicted_gap,
                "target_gap": target_gap,
                "exact_gap_match": predicted_gap == target_gap,
                "absolute_gap_error": abs(predicted_gap - target_gap),
                "confidence": response.get("confidence"),
                "explanation": response.get("explanation", ""),
            }
        )

    output_path = results_dir / "response_scores.csv"
    fieldnames = sorted({key for row in rows for key in row.keys()}) if rows else [
        "case_id", "response_path", "parse_success", "error"
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    parse_success = sum(bool(row.get("parse_success")) for row in rows)
    exact = sum(bool(row.get("exact_value_match")) for row in rows)

    print("RESPONSE SCORING COMPLETED")
    print(f"Responses:     {len(rows):,}")
    print(f"Parsed:        {parse_success:,}")
    print(f"Exact matches: {exact:,}")
    print(f"Output:        {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
