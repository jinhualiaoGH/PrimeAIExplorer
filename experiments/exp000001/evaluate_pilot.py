"""Evaluate the EXP-000001 five-case memory-window pilot.

The evaluator supports:

1. A canonical JSON array containing case_id and response fields.
2. A JSON array of bare response objects.
3. Consecutive standalone JSON objects, as used in the initial manual pilot.

The evaluator never sends data to an external service.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from statistics import mean
from typing import Any, Iterable, Sequence


EXPERIMENT_ID = "EXP-000001"
EVALUATOR_VERSION = "1.0.0"

PILOT_CASE_ORDER = (
    "CASE-W004-0001",
    "CASE-W008-0001",
    "CASE-W016-0001",
    "CASE-W032-0001",
    "CASE-W064-0001",
)


def utc_now_iso() -> str:
    """Return an ISO 8601 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest of UTF-8 text."""

    return sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    """Read one ordinary JSON document."""

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text_atomic(path: Path, payload: str) -> None:
    """Write text atomically."""

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
    """Write formatted JSON atomically."""

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


def parse_json_values(path: Path) -> list[Any]:
    """Parse an array or a stream of consecutive JSON values.

    This supports the current pilot file, where five response objects may
    appear one after another rather than inside one JSON array.
    """

    if not path.exists():
        raise FileNotFoundError(f"Response file does not exist: {path}")

    text = path.read_text(encoding="utf-8-sig").strip()

    if not text:
        raise ValueError("Response file is empty.")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        position = 0
        values: list[Any] = []

        while position < len(text):
            while position < len(text) and text[position].isspace():
                position += 1

            if position >= len(text):
                break

            value, next_position = decoder.raw_decode(
                text,
                position,
            )
            values.append(value)
            position = next_position

        if not values:
            raise ValueError(
                "No JSON response objects could be parsed."
            )

        return values

    if isinstance(parsed, list):
        return parsed

    return [parsed]


def normalize_response_records(
    raw_values: Sequence[Any],
) -> list[dict[str, Any]]:
    """Normalize response formats into case-linked records."""

    if len(raw_values) != len(PILOT_CASE_ORDER):
        raise ValueError(
            "The pilot evaluator expects exactly five response records; "
            f"found {len(raw_values)}."
        )

    normalized: list[dict[str, Any]] = []

    for position, raw_value in enumerate(raw_values):
        if not isinstance(raw_value, dict):
            raise TypeError(
                f"Response {position + 1} is not a JSON object."
            )

        expected_case_id = PILOT_CASE_ORDER[position]

        if "case_id" in raw_value:
            case_id = str(raw_value["case_id"])

            if case_id != expected_case_id:
                raise ValueError(
                    "Response order or case identity mismatch: "
                    f"expected {expected_case_id}, found {case_id}."
                )

            response = raw_value.get("response")

            if response is None and all(
                key in raw_value
                for key in (
                    "prediction",
                    "confidence",
                    "explanation",
                )
            ):
                response = {
                    "prediction": raw_value["prediction"],
                    "confidence": raw_value["confidence"],
                    "explanation": raw_value["explanation"],
                }

            model = raw_value.get(
                "model",
                "GPT-5.6 Thinking",
            )
            collection_mode = raw_value.get(
                "collection_mode",
                "manual_chat",
            )
            collected_at = raw_value.get(
                "collected_at",
                "2026-07-25",
            )
        else:
            case_id = expected_case_id
            response = raw_value
            model = "GPT-5.6 Thinking"
            collection_mode = "manual_chat"
            collected_at = "2026-07-25"

        if not isinstance(response, dict):
            raise TypeError(
                f"{case_id} does not contain a response object."
            )

        normalized.append(
            {
                "case_id": case_id,
                "model": model,
                "collection_mode": collection_mode,
                "collected_at": collected_at,
                "response": response,
            }
        )

    return normalized


def index_cases(
    cases: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Create a unique case index."""

    index: dict[str, dict[str, Any]] = {}

    for case in cases:
        case_id = str(case.get("case_id", "")).strip()

        if not case_id:
            raise ValueError("Dataset case is missing case_id.")

        if case_id in index:
            raise ValueError(f"Duplicate dataset case: {case_id}")

        index[case_id] = case

    return index


def validate_integer(
    value: Any,
    *,
    field_name: str,
) -> int:
    """Validate a genuine integer, excluding booleans."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer.")

    return value


def classify_observable_strategy(explanation: str) -> str:
    """Classify only the strategy visible in the written explanation."""

    lowered = explanation.lower()

    recognition_patterns = (
        "matches consecutive prime gaps",
        "beginning at",
        "recognized",
        "known sequence",
        "exact sequence",
    )

    frequency_patterns = (
        "common small gap",
        "common small even gap",
        "common gap",
        "frequent gap",
    )

    terminal_patterns = (
        "terminal gap",
        "after 4",
        "following the observed",
        "following the sequence",
    )

    if any(pattern in lowered for pattern in recognition_patterns):
        return "sequence_recognition_claim"

    if any(pattern in lowered for pattern in frequency_patterns):
        if any(pattern in lowered for pattern in terminal_patterns):
            return "frequency_and_local_heuristic"

        return "frequency_heuristic"

    if any(pattern in lowered for pattern in terminal_patterns):
        return "local_continuation_heuristic"

    if not explanation.strip():
        return "no_explanation"

    return "other_explanation"


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    """Objective evaluation for one pilot response."""

    case_id: str
    pair_id: str
    window_size: int
    model: str
    collection_mode: str
    collected_at: str

    prediction: int
    ground_truth: int
    exact_match: bool
    absolute_error: int
    signed_error: int

    confidence: int
    confidence_probability: float
    brier_score: float

    explanation: str
    explanation_characters: int
    explanation_words: int
    observable_strategy: str

    target_left_prime: int
    target_right_prime: int
    response_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_record(
    *,
    case: dict[str, Any],
    response_record: dict[str, Any],
) -> CaseEvaluation:
    """Evaluate one normalized response against hidden ground truth."""

    response = response_record["response"]

    required_fields = {
        "prediction",
        "confidence",
        "explanation",
    }

    missing = sorted(required_fields - set(response))

    if missing:
        raise ValueError(
            f"{response_record['case_id']} is missing response fields: "
            + ", ".join(missing)
        )

    prediction = validate_integer(
        response["prediction"],
        field_name="prediction",
    )
    confidence = validate_integer(
        response["confidence"],
        field_name="confidence",
    )

    if confidence < 0 or confidence > 100:
        raise ValueError(
            f"{response_record['case_id']} confidence must be 0-100."
        )

    explanation = response["explanation"]

    if not isinstance(explanation, str):
        raise TypeError("explanation must be a string.")

    ground_truth = validate_integer(
        case["ground_truth"],
        field_name="ground_truth",
    )

    exact_match = prediction == ground_truth
    confidence_probability = confidence / 100.0

    outcome = 1.0 if exact_match else 0.0
    brier_score = (confidence_probability - outcome) ** 2

    response_payload = {
        "prediction": prediction,
        "confidence": confidence,
        "explanation": explanation,
    }

    words = re.findall(r"\b[\w'-]+\b", explanation)

    return CaseEvaluation(
        case_id=response_record["case_id"],
        pair_id=str(case["pair_id"]),
        window_size=validate_integer(
            case["window_size"],
            field_name="window_size",
        ),
        model=str(response_record["model"]),
        collection_mode=str(
            response_record["collection_mode"]
        ),
        collected_at=str(response_record["collected_at"]),
        prediction=prediction,
        ground_truth=ground_truth,
        exact_match=exact_match,
        absolute_error=abs(prediction - ground_truth),
        signed_error=prediction - ground_truth,
        confidence=confidence,
        confidence_probability=confidence_probability,
        brier_score=brier_score,
        explanation=explanation,
        explanation_characters=len(explanation),
        explanation_words=len(words),
        observable_strategy=classify_observable_strategy(
            explanation
        ),
        target_left_prime=validate_integer(
            case["target_left_prime"],
            field_name="target_left_prime",
        ),
        target_right_prime=validate_integer(
            case["target_right_prime"],
            field_name="target_right_prime",
        ),
        response_sha256=sha256_text(
            canonical_json(response_payload)
        ),
    )


def build_summary(
    evaluations: Sequence[CaseEvaluation],
) -> dict[str, Any]:
    """Build overall and per-window descriptive summaries."""

    if not evaluations:
        raise ValueError("No evaluations were supplied.")

    exact_values = [
        1 if evaluation.exact_match else 0
        for evaluation in evaluations
    ]

    by_window: dict[str, Any] = {}

    for evaluation in sorted(
        evaluations,
        key=lambda item: item.window_size,
    ):
        by_window[str(evaluation.window_size)] = {
            "case_id": evaluation.case_id,
            "prediction": evaluation.prediction,
            "ground_truth": evaluation.ground_truth,
            "exact_match": evaluation.exact_match,
            "absolute_error": evaluation.absolute_error,
            "confidence": evaluation.confidence,
            "brier_score": evaluation.brier_score,
            "observable_strategy": (
                evaluation.observable_strategy
            ),
        }

    strategy_counts: dict[str, int] = {}

    for evaluation in evaluations:
        strategy_counts[evaluation.observable_strategy] = (
            strategy_counts.get(
                evaluation.observable_strategy,
                0,
            )
            + 1
        )

    confidence_values = [
        evaluation.confidence
        for evaluation in evaluations
    ]

    return {
        "pilot_case_count": len(evaluations),
        "accuracy": mean(exact_values),
        "correct_count": sum(exact_values),
        "incorrect_count": (
            len(evaluations) - sum(exact_values)
        ),
        "mean_absolute_error": mean(
            evaluation.absolute_error
            for evaluation in evaluations
        ),
        "mean_confidence": mean(confidence_values),
        "minimum_confidence": min(confidence_values),
        "maximum_confidence": max(confidence_values),
        "mean_brier_score": mean(
            evaluation.brier_score
            for evaluation in evaluations
        ),
        "strategy_counts": dict(
            sorted(strategy_counts.items())
        ),
        "by_window": by_window,
    }


def write_evaluations_csv(
    path: Path,
    evaluations: Sequence[CaseEvaluation],
) -> None:
    """Write compact evaluation results."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")

    fieldnames = [
        "case_id",
        "pair_id",
        "window_size",
        "model",
        "prediction",
        "ground_truth",
        "exact_match",
        "absolute_error",
        "signed_error",
        "confidence",
        "confidence_probability",
        "brier_score",
        "observable_strategy",
        "explanation_characters",
        "explanation_words",
        "target_left_prime",
        "target_right_prime",
        "response_sha256",
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

            for evaluation in evaluations:
                row = evaluation.to_dict()
                writer.writerow(
                    {
                        field: row[field]
                        for field in fieldnames
                    }
                )

        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def build_markdown_report(
    *,
    evaluations: Sequence[CaseEvaluation],
    summary: dict[str, Any],
    responses_path: Path,
    cases_path: Path,
) -> str:
    """Build the first real EXP-000001 pilot report."""

    lines = [
        "# EXP-000001 Pilot Evaluation Report",
        "",
        f"Evaluator version: {EVALUATOR_VERSION}",
        f"Generated: {utc_now_iso()}",
        "",
        "## Scientific Question",
        "",
        (
            "How does the visible prime-gap observation window affect "
            "prediction, confidence, and observable explanation strategy?"
        ),
        "",
        "## Pilot Design",
        "",
        "- One shared hidden prediction target",
        "- Five observation windows: 4, 8, 16, 32, and 64",
        "- One independent manual ChatGPT conversation per window",
        "- Ground truth withheld during model collection",
        "- No API call or automated model connector",
        "",
        "## Objective Results",
        "",
        "| Window | Prediction | Truth | Correct | Confidence | "
        "Absolute Error | Brier Score | Observable Strategy |",
        "|---:|---:|---:|:---:|---:|---:|---:|---|",
    ]

    for evaluation in sorted(
        evaluations,
        key=lambda item: item.window_size,
    ):
        lines.append(
            "| "
            f"{evaluation.window_size} | "
            f"{evaluation.prediction} | "
            f"{evaluation.ground_truth} | "
            f"{'Yes' if evaluation.exact_match else 'No'} | "
            f"{evaluation.confidence} | "
            f"{evaluation.absolute_error} | "
            f"{evaluation.brier_score:.4f} | "
            f"{evaluation.observable_strategy} |"
        )

    lines.extend(
        [
            "",
            "## Pilot Summary",
            "",
            (
                f"- Correct predictions: "
                f"{summary['correct_count']}/"
                f"{summary['pilot_case_count']}"
            ),
            f"- Accuracy: {summary['accuracy']:.1%}",
            (
                f"- Mean absolute error: "
                f"{summary['mean_absolute_error']:.3f}"
            ),
            (
                f"- Mean reported confidence: "
                f"{summary['mean_confidence']:.1f}"
            ),
            (
                f"- Confidence range: "
                f"{summary['minimum_confidence']}â€“"
                f"{summary['maximum_confidence']}"
            ),
            (
                f"- Mean Brier score: "
                f"{summary['mean_brier_score']:.4f}"
            ),
            "",
            "## Observable Strategy Counts",
            "",
        ]
    )

    for strategy, count in summary["strategy_counts"].items():
        lines.append(f"- `{strategy}`: {count}")

    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            (
                "Strategy labels are rule-based descriptions of the written "
                "explanations. They do not reveal or verify the model's "
                "private internal reasoning."
            ),
            "",
            (
                "Because this pilot contains one shared target and only five "
                "responses, it cannot establish a general memory-performance "
                "relationship. It validates the experimental workflow and "
                "identifies hypotheses for the larger study."
            ),
            "",
            "## Provenance",
            "",
            f"- Cases: `{cases_path.resolve()}`",
            f"- Responses: `{responses_path.resolve()}`",
            f"- Experiment: `{EXPERIMENT_ID}`",
            f"- Evaluator: `{EVALUATOR_VERSION}`",
            "",
            "## Guiding Principle",
            "",
            "Make observations first. Draw conclusions second.",
            "",
        ]
    )

    return "\n".join(lines)


def evaluate_pilot(
    *,
    cases_path: Path,
    responses_path: Path,
    output_directory: Path,
) -> dict[str, Any]:
    """Execute the complete pilot evaluation."""

    cases = read_json(cases_path)

    if not isinstance(cases, list):
        raise TypeError("Cases file must contain a JSON array.")

    case_index = index_cases(cases)

    raw_responses = parse_json_values(responses_path)
    response_records = normalize_response_records(
        raw_responses
    )

    evaluations: list[CaseEvaluation] = []

    for response_record in response_records:
        case_id = response_record["case_id"]

        try:
            case = case_index[case_id]
        except KeyError as error:
            raise KeyError(
                f"Pilot case was not found in dataset: {case_id}"
            ) from error

        evaluations.append(
            evaluate_record(
                case=case,
                response_record=response_record,
            )
        )

    evaluations = sorted(
        evaluations,
        key=lambda item: item.window_size,
    )

    target_pairs = {
        (
            evaluation.target_left_prime,
            evaluation.target_right_prime,
            evaluation.ground_truth,
        )
        for evaluation in evaluations
    }

    if len(target_pairs) != 1:
        raise AssertionError(
            "Pilot cases do not share one hidden prediction target."
        )

    summary = build_summary(evaluations)

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "experiment_id": EXPERIMENT_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "generated_at_utc": utc_now_iso(),
        "source": {
            "cases_path": str(cases_path.resolve()),
            "responses_path": str(responses_path.resolve()),
            "responses_sha256": sha256_text(
                responses_path.read_text(
                    encoding="utf-8-sig"
                )
            ),
        },
        "design": {
            "paired_target": True,
            "window_sizes": [
                evaluation.window_size
                for evaluation in evaluations
            ],
            "response_count": len(evaluations),
        },
        "evaluations": [
            evaluation.to_dict()
            for evaluation in evaluations
        ],
        "summary": summary,
        "limitations": [
            "Only one shared hidden target was evaluated.",
            "Only one response was collected per window.",
            "Responses were collected manually.",
            (
                "Observable strategy labels are based on response text "
                "and do not expose private reasoning."
            ),
        ],
    }

    payload["integrity"] = {
        "algorithm": "SHA-256",
        "evaluation_sha256": sha256_text(
            canonical_json(payload)
        ),
    }

    write_json_atomic(
        output_directory / "pilot_evaluation.json",
        payload,
    )

    write_evaluations_csv(
        output_directory / "pilot_evaluation.csv",
        evaluations,
    )

    report = build_markdown_report(
        evaluations=evaluations,
        summary=summary,
        responses_path=responses_path,
        cases_path=cases_path,
    )

    write_text_atomic(
        output_directory / "Pilot_Report.md",
        report,
    )

    return payload


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the EXP-000001 five-case pilot."
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
        help="Canonical EXP-000001 cases file.",
    )
    parser.add_argument(
        "--responses",
        type=Path,
        default=(
            Path("experiments")
            / "exp000001"
            / "pilot_001"
            / "responses.json"
        ),
        help="Collected pilot responses.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            Path("experiments")
            / "exp000001"
            / "pilot_001"
        ),
        help="Pilot output directory.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    result = evaluate_pilot(
        cases_path=arguments.cases,
        responses_path=arguments.responses,
        output_directory=arguments.output,
    )

    summary = result["summary"]

    print()
    print("=" * 72)
    print("PrimeAIExplorer EXP-000001 Evaluator v1.0")
    print("=" * 72)
    print(f"Responses:         {summary['pilot_case_count']}")
    print(
        f"Correct:           "
        f"{summary['correct_count']}/"
        f"{summary['pilot_case_count']}"
    )
    print(f"Accuracy:          {summary['accuracy']:.1%}")
    print(
        f"Mean abs. error:   "
        f"{summary['mean_absolute_error']:.3f}"
    )
    print(
        f"Mean confidence:   "
        f"{summary['mean_confidence']:.1f}"
    )
    print(
        f"Mean Brier score:  "
        f"{summary['mean_brier_score']:.4f}"
    )
    print(
        "Evaluation hash:   "
        f"{result['integrity']['evaluation_sha256']}"
    )
    print(f"Output:            {arguments.output.resolve()}")
    print()
    print("EXP-000001 PILOT EVALUATION PASSED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
