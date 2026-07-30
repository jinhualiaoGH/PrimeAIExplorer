from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_concatenated_json(text: str) -> list[dict[str, Any]]:
    """Parse one or more consecutive JSON objects."""

    decoder = json.JSONDecoder()
    position = 0
    records: list[dict[str, Any]] = []

    while position < len(text):
        while position < len(text) and text[position].isspace():
            position += 1

        if position >= len(text):
            break

        value, next_position = decoder.raw_decode(text, position)

        if not isinstance(value, dict):
            raise ValueError(
                f"Expected a JSON object at character {position}; "
                f"found {type(value).__name__}."
            )

        records.append(value)
        position = next_position

    return records


def normalize_responses(
    *,
    source_path: Path,
    prompts_directory: Path,
    output_path: Path,
) -> None:
    # utf-8-sig removes an optional UTF-8 BOM safely.
    source_text = source_path.read_text(encoding="utf-8-sig")
    raw_responses = parse_concatenated_json(source_text)

    prompt_paths = sorted(
        prompts_directory.glob("CASE-*.txt"),
        key=lambda path: path.name,
    )

    case_ids = [
        path.stem
        for path in prompt_paths
    ]

    if len(raw_responses) != len(case_ids):
        raise ValueError(
            "Response/prompt count mismatch: "
            f"{len(raw_responses)} responses versus "
            f"{len(case_ids)} prompt files."
        )

    normalized: list[dict[str, Any]] = []

    for case_id, response in zip(case_ids, raw_responses):
        prediction = response.get("prediction")
        confidence = response.get("confidence")
        explanation = response.get("explanation")

        if isinstance(prediction, bool) or not isinstance(prediction, int):
            raise ValueError(
                f"{case_id}: prediction must be an integer."
            )

        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, int)
            or not 0 <= confidence <= 100
        ):
            raise ValueError(
                f"{case_id}: confidence must be an integer from 0 to 100."
            )

        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError(
                f"{case_id}: explanation must be nonempty text."
            )

        normalized.append(
            {
                "case_id": case_id,
                "prediction": prediction,
                "confidence": confidence,
                "explanation": explanation.strip(),
            }
        )

    payload = {
        "format": "PrimeAIExplorer.aggregate_responses",
        "format_version": "1.0.0",
        "source_file": source_path.name,
        "responses": normalized,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = output_path.with_name(
        output_path.name + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    temporary_path.replace(output_path)

    print("[PASS] Response normalization complete")
    print(f"[PASS] Responses: {len(normalized)}")

    for item in normalized:
        print(
            f"[PASS] {item['case_id']}: "
            f"prediction={item['prediction']} "
            f"confidence={item['confidence']}"
        )

    print(f"[PASS] Output: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize concatenated PrimeAIExplorer pilot responses "
            "into one canonical aggregate JSON document."
        )
    )

    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Original concatenated responses.json file.",
    )

    parser.add_argument(
        "--prompts",
        required=True,
        type=Path,
        help="Directory containing ordered CASE-*.txt prompt files.",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination canonical responses JSON file.",
    )

    arguments = parser.parse_args()

    normalize_responses(
        source_path=arguments.source.resolve(),
        prompts_directory=arguments.prompts.resolve(),
        output_path=arguments.output.resolve(),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
