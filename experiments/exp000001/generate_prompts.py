"""Generate canonical model-visible prompts for EXP-000001.

Ground-truth values and target-prime metadata are never included in the
model-visible prompt artifacts.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Sequence


EXPERIMENT_ID = "EXP-000001"
PROMPT_SET_ID = "PROMPTSET-EXP000001-001"
PROMPT_SET_VERSION = "0.1.0"

SYSTEM_MESSAGE = (
    "You are participating in a controlled numerical continuation "
    "experiment. Follow the response format exactly."
)

RESPONSE_INSTRUCTION = """Return JSON only using this exact structure:

{
  "prediction": <integer>,
  "confidence": <integer from 0 to 100>,
  "explanation": "<brief explanation>"
}"""


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
        raise FileNotFoundError(f"Input file does not exist: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


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
    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    write_text_atomic(path, payload)


@dataclass(frozen=True, slots=True)
class PromptRecord:
    prompt_record_id: str
    prompt_set_id: str
    prompt_set_version: str
    experiment_id: str
    case_id: str
    pair_id: str
    window_size: int
    system_message: str
    user_message: str
    response_format: str
    prompt_sha256: str
    source_case_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_user_message(
    *,
    observed_gaps: Sequence[int],
    window_size: int,
) -> str:
    gap_text = " ".join(str(value) for value in observed_gaps)

    return (
        "You are given a sequence of consecutive prime gaps.\n\n"
        f"Observation window size: {window_size}\n\n"
        "Observed gaps:\n"
        f"{gap_text}\n\n"
        "Predict the next prime gap.\n\n"
        f"{RESPONSE_INSTRUCTION}"
    )


def build_prompt_record(
    case: dict[str, Any],
) -> PromptRecord:
    required_fields = {
        "case_id",
        "pair_id",
        "experiment_id",
        "window_size",
        "observed_gaps",
    }

    missing = sorted(required_fields - set(case))

    if missing:
        raise ValueError(
            f"Case is missing required fields: {', '.join(missing)}"
        )

    observed = case["observed_gaps"]

    if not isinstance(observed, list) or not observed:
        raise ValueError(
            f"{case['case_id']} has no observed gaps."
        )

    if len(observed) != case["window_size"]:
        raise ValueError(
            f"{case['case_id']} has an invalid observation length."
        )

    user_message = build_user_message(
        observed_gaps=observed,
        window_size=case["window_size"],
    )

    scientific_prompt_payload = {
        "system_message": SYSTEM_MESSAGE,
        "user_message": user_message,
        "response_format": "json_object",
    }

    return PromptRecord(
        prompt_record_id=f"PR-{case['case_id']}",
        prompt_set_id=PROMPT_SET_ID,
        prompt_set_version=PROMPT_SET_VERSION,
        experiment_id=case["experiment_id"],
        case_id=case["case_id"],
        pair_id=case["pair_id"],
        window_size=case["window_size"],
        system_message=SYSTEM_MESSAGE,
        user_message=user_message,
        response_format="json_object",
        prompt_sha256=sha256_text(
            canonical_json(scientific_prompt_payload)
        ),
        source_case_sha256=sha256_text(
            canonical_json(case)
        ),
    )


def validate_no_answer_leakage(
    *,
    case: dict[str, Any],
    prompt: PromptRecord,
) -> None:
    prohibited_field_names = (
        "ground_truth",
        "target_left_prime",
        "target_right_prime",
        "target_gap_index_zero_based",
        "target_prime_index_one_based",
    )

    visible_text = (
        prompt.system_message
        + "\n"
        + prompt.user_message
    )

    lowered = visible_text.lower()

    for field_name in prohibited_field_names:
        if field_name.lower() in lowered:
            raise AssertionError(
                f"Prompt leaks prohibited field name: {field_name}"
            )

    # Validate structure rather than searching for the numeric answer because
    # the same number may legitimately appear in the observed sequence.
    visible_payload = prompt.to_dict()

    for field_name in prohibited_field_names:
        if field_name in visible_payload:
            raise AssertionError(
                f"Prompt record leaks prohibited field: {field_name}"
            )

    if "ground_truth" not in case:
        raise AssertionError(
            "Source case does not contain ground truth for evaluation."
        )


def write_prompts_csv(
    path: Path,
    prompts: Sequence[PromptRecord],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")

    fieldnames = [
        "prompt_record_id",
        "prompt_set_id",
        "prompt_set_version",
        "experiment_id",
        "case_id",
        "pair_id",
        "window_size",
        "prompt_sha256",
        "source_case_sha256",
        "response_format",
    ]

    try:
        with temporary.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fieldnames,
            )
            writer.writeheader()

            for prompt in prompts:
                row = prompt.to_dict()
                writer.writerow(
                    {
                        key: row[key]
                        for key in fieldnames
                    }
                )

        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def generate_prompts(
    *,
    cases_path: Path,
    output_directory: Path,
) -> dict[str, Any]:
    cases = read_json(cases_path)

    if not isinstance(cases, list) or not cases:
        raise ValueError("Cases JSON must contain a non-empty list.")

    prompts: list[PromptRecord] = []

    for case in cases:
        prompt = build_prompt_record(case)
        validate_no_answer_leakage(
            case=case,
            prompt=prompt,
        )
        prompts.append(prompt)

    prompt_ids = [
        prompt.prompt_record_id
        for prompt in prompts
    ]

    if len(prompt_ids) != len(set(prompt_ids)):
        raise AssertionError("Duplicate prompt IDs detected.")

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    text_directory = output_directory / "text"
    text_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    prompt_payload = [
        prompt.to_dict()
        for prompt in prompts
    ]

    for prompt in prompts:
        text_payload = (
            f"SYSTEM\n"
            f"{prompt.system_message}\n\n"
            f"USER\n"
            f"{prompt.user_message}\n"
        )

        write_text_atomic(
            text_directory / f"{prompt.case_id}.txt",
            text_payload,
        )

    write_json_atomic(
        output_directory / "prompts.json",
        prompt_payload,
    )

    write_prompts_csv(
        output_directory / "prompts.csv",
        prompts,
    )

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "prompt_set_id": PROMPT_SET_ID,
        "prompt_set_version": PROMPT_SET_VERSION,
        "generated_at_utc": utc_now_iso(),
        "generator": (
            "experiments.exp000001.generate_prompts"
        ),
        "generator_version": "0.1.0",
        "source_cases": str(cases_path.resolve()),
        "prompt_count": len(prompts),
        "window_counts": {
            str(window): sum(
                1
                for prompt in prompts
                if prompt.window_size == window
            )
            for window in sorted(
                {
                    prompt.window_size
                    for prompt in prompts
                }
            )
        },
        "response_contract": {
            "type": "json_object",
            "required_fields": [
                "prediction",
                "confidence",
                "explanation",
            ],
        },
        "leakage_policy": {
            "ground_truth_visible": False,
            "target_prime_metadata_visible": False,
        },
        "integrity": {
            "algorithm": "SHA-256",
            "prompts_sha256": sha256_text(
                canonical_json(prompt_payload)
            ),
        },
    }

    write_json_atomic(
        output_directory / "prompt_manifest.json",
        manifest,
    )

    return manifest


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate model-visible prompts for EXP-000001."
        )
    )

    parser.add_argument(
        "--cases",
        type=Path,
        default=(
            Path("datasets")
            / "EXP-000001"
            / "cases.json"
        ),
        help="Path to the generated cases JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            Path("prompts")
            / "EXP-000001"
        ),
        help="Output directory.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    manifest = generate_prompts(
        cases_path=arguments.cases,
        output_directory=arguments.output,
    )

    print()
    print("=" * 72)
    print("PrimeAIExplorer EXP-000001 Prompt Generator")
    print("=" * 72)
    print(f"Experiment:       {manifest['experiment_id']}")
    print(f"Prompt set:       {manifest['prompt_set_id']}")
    print(f"Prompt count:     {manifest['prompt_count']}")
    print(
        "Window counts:    "
        + ", ".join(
            f"{window}={count}"
            for window, count
            in manifest["window_counts"].items()
        )
    )
    print(
        "Ground truth visible: "
        f"{manifest['leakage_policy']['ground_truth_visible']}"
    )
    print(
        f"Prompts SHA-256:  "
        f"{manifest['integrity']['prompts_sha256']}"
    )
    print(f"Output:           {arguments.output.resolve()}")
    print()
    print("EXP-000001 PROMPT GENERATION PASSED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())