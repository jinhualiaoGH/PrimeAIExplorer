"""Prepare EXP-000001 Pilot 002 with multiple hidden targets.

Pilot 002 uses five paired prediction targets and five observation windows:

    5 targets x 5 windows = 25 model-visible prompts

The source dataset and canonical prompt artifacts are reused without exposing
ground truth to the response-collection package.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any, Sequence


EXPERIMENT_ID = "EXP-000001"
PILOT_ID = "PILOT-002"
PILOT_VERSION = "0.1.0"

DEFAULT_PAIR_IDS = (
    "PAIR-0002",
    "PAIR-0003",
    "PAIR-0004",
    "PAIR-0005",
    "PAIR-0006",
)

EXPECTED_WINDOWS = (4, 8, 16, 32, 64)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")

    try:
        temporary.write_text(
            payload,
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def write_json_atomic(path: Path, value: Any) -> None:
    write_text_atomic(
        path,
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
    )


def parse_pair_ids(value: str) -> tuple[str, ...]:
    pair_ids = tuple(
        item.strip()
        for item in value.split(",")
        if item.strip()
    )

    if not pair_ids:
        raise argparse.ArgumentTypeError(
            "At least one pair ID is required."
        )

    if len(pair_ids) != len(set(pair_ids)):
        raise argparse.ArgumentTypeError(
            "Pair IDs must be unique."
        )

    return pair_ids


def prepare_pilot(
    *,
    cases_path: Path,
    prompt_directory: Path,
    output_directory: Path,
    pair_ids: Sequence[str],
) -> dict[str, Any]:
    cases = read_json(cases_path)

    if not isinstance(cases, list):
        raise TypeError("Cases file must contain a JSON array.")

    selected_cases = [
        case
        for case in cases
        if case.get("pair_id") in pair_ids
    ]

    expected_case_count = len(pair_ids) * len(EXPECTED_WINDOWS)

    if len(selected_cases) != expected_case_count:
        raise ValueError(
            f"Expected {expected_case_count} selected cases; "
            f"found {len(selected_cases)}."
        )

    selected_cases = sorted(
        selected_cases,
        key=lambda case: (
            pair_ids.index(case["pair_id"]),
            case["window_size"],
        ),
    )

    for pair_id in pair_ids:
        pair_cases = [
            case
            for case in selected_cases
            if case["pair_id"] == pair_id
        ]

        windows = tuple(
            sorted(case["window_size"] for case in pair_cases)
        )

        if windows != EXPECTED_WINDOWS:
            raise ValueError(
                f"{pair_id} does not contain the expected windows."
            )

        target_identity = {
            (
                case["target_gap_index_zero_based"],
                case["ground_truth"],
                case["target_left_prime"],
                case["target_right_prime"],
            )
            for case in pair_cases
        }

        if len(target_identity) != 1:
            raise ValueError(
                f"{pair_id} does not share one prediction target."
            )

    text_output = output_directory / "text"
    text_output.mkdir(parents=True, exist_ok=True)

    model_visible_index: list[dict[str, Any]] = []
    response_template: list[dict[str, Any]] = []

    for case in selected_cases:
        case_id = case["case_id"]
        source_prompt = prompt_directory / f"{case_id}.txt"

        if not source_prompt.exists():
            raise FileNotFoundError(
                f"Canonical prompt does not exist: {source_prompt}"
            )

        destination = text_output / source_prompt.name
        shutil.copyfile(source_prompt, destination)

        prompt_text = destination.read_text(encoding="utf-8-sig")

        model_visible_index.append(
            {
                "case_id": case_id,
                "pair_id": case["pair_id"],
                "window_size": case["window_size"],
                "prompt_file": f"text/{case_id}.txt",
                "prompt_sha256": sha256_text(prompt_text),
            }
        )

        response_template.append(
            {
                "case_id": case_id,
                "pair_id": case["pair_id"],
                "window_size": case["window_size"],
                "model": "GPT-5.6 Thinking",
                "collection_mode": "manual_chat",
                "collected_at": None,
                "response": None,
            }
        )

    visible_payload = {
        "experiment_id": EXPERIMENT_ID,
        "pilot_id": PILOT_ID,
        "pilot_version": PILOT_VERSION,
        "pair_count": len(pair_ids),
        "window_sizes": list(EXPECTED_WINDOWS),
        "case_count": len(model_visible_index),
        "cases": model_visible_index,
    }

    write_json_atomic(
        output_directory / "pilot_manifest.json",
        {
            **visible_payload,
            "generated_at_utc": utc_now_iso(),
            "collection_protocol": {
                "fresh_conversation_per_case": True,
                "ground_truth_visible": False,
                "prior_responses_visible": False,
                "response_format": "json_object",
            },
            "integrity": {
                "algorithm": "SHA-256",
                "model_visible_index_sha256": sha256_text(
                    canonical_json(model_visible_index)
                ),
            },
        },
    )

    write_json_atomic(
        output_directory / "responses.json",
        response_template,
    )

    collection_order = [
        "# EXP-000001 Pilot 002 Collection Order",
        "",
        "Use one fresh conversation for every case.",
        "",
        "Do not reveal the case ID, pair ID, or ground truth to the model.",
        "",
    ]

    for number, item in enumerate(model_visible_index, start=1):
        collection_order.append(
            f"{number:02d}. `{item['case_id']}` "
            f"(target {item['pair_id']}, "
            f"window {item['window_size']})"
        )

    collection_order.extend(
        [
            "",
            "After each response, preserve exactly:",
            "",
            "- prediction",
            "- confidence",
            "- explanation",
            "",
        ]
    )

    write_text_atomic(
        output_directory / "Collection_Order.md",
        "\n".join(collection_order),
    )

    return visible_payload


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the 25-case EXP-000001 multiple-target pilot."
        )
    )

    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("datasets/EXP-000001/cases.json"),
    )
    parser.add_argument(
        "--prompts",
        type=Path,
        default=Path("prompts/EXP-000001/text"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "experiments/exp000001/pilot_002"
        ),
    )
    parser.add_argument(
        "--pairs",
        type=parse_pair_ids,
        default=DEFAULT_PAIR_IDS,
        help="Comma-separated paired target identifiers.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    result = prepare_pilot(
        cases_path=arguments.cases,
        prompt_directory=arguments.prompts,
        output_directory=arguments.output,
        pair_ids=arguments.pairs,
    )

    print()
    print("=" * 72)
    print("PrimeAIExplorer EXP-000001 Pilot 002 Preparation")
    print("=" * 72)
    print(f"Pilot:             {result['pilot_id']}")
    print(f"Hidden targets:    {result['pair_count']}")
    print(
        "Window sizes:     "
        + ", ".join(
            str(value)
            for value in result["window_sizes"]
        )
    )
    print(f"Total prompts:     {result['case_count']}")
    print(f"Output:            {arguments.output.resolve()}")
    print()
    print("EXP-000001 PILOT 002 PREPARATION PASSED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())