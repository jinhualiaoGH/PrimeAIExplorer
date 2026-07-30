"""Manage manual response collection for EXP-000001 pilots.

This tool supports:

- progress inspection
- next-case selection
- prompt display
- validated response entry
- atomic response-file updates
- duplicate protection
- final collection validation

It performs no model calls and exposes no hidden ground truth.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Sequence


REQUIRED_RESPONSE_FIELDS = (
    "prediction",
    "confidence",
    "explanation",
)


def utc_now_iso() -> str:
    """Return an ISO 8601 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    """Read one JSON document."""

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json_atomic(path: Path, value: Any) -> None:
    """Write JSON atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")

    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
            allow_nan=False,
        )
        + "\n"
    )

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


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load and validate response-template records."""

    value = read_json(path)

    if not isinstance(value, list) or not value:
        raise ValueError(
            "Response file must contain a non-empty JSON array."
        )

    records: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()

    for position, record in enumerate(value, start=1):
        if not isinstance(record, dict):
            raise TypeError(
                f"Record {position} is not a JSON object."
            )

        case_id = str(record.get("case_id", "")).strip()

        if not case_id:
            raise ValueError(
                f"Record {position} is missing case_id."
            )

        if case_id in seen_case_ids:
            raise ValueError(
                f"Duplicate case identifier: {case_id}"
            )

        seen_case_ids.add(case_id)
        records.append(record)

    return records


def is_complete(record: dict[str, Any]) -> bool:
    """Return whether a record has a collected response."""

    return isinstance(record.get("response"), dict)


def validate_response(value: Any) -> dict[str, Any]:
    """Validate one canonical manual response object."""

    if not isinstance(value, dict):
        raise TypeError(
            "The model response must be a JSON object."
        )

    missing = [
        field
        for field in REQUIRED_RESPONSE_FIELDS
        if field not in value
    ]

    if missing:
        raise ValueError(
            "Response is missing required fields: "
            + ", ".join(missing)
        )

    prediction = value["prediction"]
    confidence = value["confidence"]
    explanation = value["explanation"]

    if isinstance(prediction, bool) or not isinstance(prediction, int):
        raise TypeError("prediction must be an integer.")

    if isinstance(confidence, bool) or not isinstance(confidence, int):
        raise TypeError("confidence must be an integer.")

    if confidence < 0 or confidence > 100:
        raise ValueError(
            "confidence must be between 0 and 100."
        )

    if not isinstance(explanation, str):
        raise TypeError("explanation must be a string.")

    if not explanation.strip():
        raise ValueError("explanation cannot be empty.")

    return {
        "prediction": prediction,
        "confidence": confidence,
        "explanation": explanation,
    }


def find_record(
    records: Sequence[dict[str, Any]],
    case_id: str,
) -> dict[str, Any]:
    """Find one case-linked response record."""

    for record in records:
        if record["case_id"] == case_id:
            return record

    raise KeyError(f"Unknown case ID: {case_id}")


def next_missing_record(
    records: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return the next record without a response."""

    for record in records:
        if not is_complete(record):
            return record

    return None


def show_progress(
    records: Sequence[dict[str, Any]],
) -> None:
    """Display collection accounting."""

    completed = [
        record
        for record in records
        if is_complete(record)
    ]
    missing = [
        record
        for record in records
        if not is_complete(record)
    ]

    print("=" * 72)
    print("EXP-000001 Manual Response Collection")
    print("=" * 72)
    print(f"Total cases:      {len(records)}")
    print(f"Completed:        {len(completed)}")
    print(f"Missing:          {len(missing)}")
    print(
        f"Progress:         "
        f"{100.0 * len(completed) / len(records):.1f}%"
    )

    by_pair: dict[str, dict[str, int]] = {}

    for record in records:
        pair_id = str(record.get("pair_id", "UNKNOWN"))

        counters = by_pair.setdefault(
            pair_id,
            {
                "completed": 0,
                "total": 0,
            },
        )
        counters["total"] += 1

        if is_complete(record):
            counters["completed"] += 1

    print()
    print("Progress by target:")

    for pair_id, counters in sorted(by_pair.items()):
        print(
            f"  {pair_id}: "
            f"{counters['completed']}/{counters['total']}"
        )

    if missing:
        print()
        print("Next missing case:")
        print(f"  {missing[0]['case_id']}")
    else:
        print()
        print("[PASS] All responses have been collected")


def show_prompt(
    *,
    pilot_directory: Path,
    case_id: str,
) -> None:
    """Display one canonical model-visible prompt."""

    prompt_path = (
        pilot_directory
        / "text"
        / f"{case_id}.txt"
    )

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file does not exist: {prompt_path}"
        )

    print("=" * 72)
    print(f"Prompt for {case_id}")
    print("=" * 72)
    print()
    print(
        prompt_path.read_text(
            encoding="utf-8-sig"
        ).rstrip()
    )
    print()


def parse_response_argument(
    *,
    response_json: str | None,
    response_file: Path | None,
) -> dict[str, Any]:
    """Read a response from a command argument, file, or standard input."""

    supplied = sum(
        value is not None
        for value in (
            response_json,
            response_file,
        )
    )

    if supplied > 1:
        raise ValueError(
            "Use either --response-json or --response-file, not both."
        )

    if response_file is not None:
        raw_text = response_file.read_text(
            encoding="utf-8-sig"
        )
    elif response_json is not None:
        raw_text = response_json
    else:
        print(
            "Paste the JSON response, then press Enter."
        )
        raw_text = input("> ")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid response JSON: {error}"
        ) from error

    return validate_response(parsed)

def read_clipboard_response() -> dict[str, Any]:
    """Read and validate one JSON response from the system clipboard."""

    import os
    import subprocess

    if os.name == "nt":
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Clipboard -Raw",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        raw_text = completed.stdout
    else:
        raise RuntimeError(
            "Clipboard collection is currently implemented for Windows."
        )

    if not raw_text.strip():
        raise ValueError("The clipboard is empty.")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Clipboard content is not valid JSON: "
            f"{error}"
        ) from error

    return validate_response(parsed)
def add_response(
    *,
    records: list[dict[str, Any]],
    case_id: str,
    response: dict[str, Any],
    overwrite: bool,
) -> dict[str, Any]:
    """Attach one validated response to its collection record."""

    record = find_record(records, case_id)

    if is_complete(record) and not overwrite:
        raise ValueError(
            f"{case_id} already has a response. "
            "Use --overwrite only for an intentional correction."
        )

    record["collected_at"] = utc_now_iso()
    record["response"] = response

    return record


def validate_collection(
    records: Sequence[dict[str, Any]],
) -> None:
    """Validate every completed collection record."""

    errors: list[str] = []

    for record in records:
        case_id = record["case_id"]

        if not is_complete(record):
            errors.append(
                f"{case_id}: response is missing"
            )
            continue

        try:
            validate_response(record["response"])
        except (TypeError, ValueError) as error:
            errors.append(
                f"{case_id}: {error}"
            )

        collected_at = record.get("collected_at")

        if not isinstance(collected_at, str) or not collected_at.strip():
            errors.append(
                f"{case_id}: collected_at is missing"
            )

    if errors:
        print("[FAIL] Collection validation errors:")

        for error in errors:
            print(f"  - {error}")

        raise ValueError(
            f"Collection contains {len(errors)} validation error(s)."
        )

    print(
        f"[PASS] All {len(records)} responses are complete and valid"
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manage manual response collection for an "
            "EXP-000001 pilot."
        )
    )

    parser.add_argument(
        "--pilot",
        type=Path,
        default=Path(
            "experiments/exp000001/pilot_002"
        ),
        help="Pilot directory.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "status",
        help="Show response-collection progress.",
    )

    next_parser = subparsers.add_parser(
        "next",
        help="Display the next missing prompt.",
    )
    next_parser.add_argument(
        "--open",
        action="store_true",
        help="Open the prompt in VS Code.",
    )

    show_parser = subparsers.add_parser(
        "show",
        help="Display a selected prompt.",
    )
    show_parser.add_argument(
        "case_id",
        help="Canonical case identifier.",
    )

    add_parser = subparsers.add_parser(
        "add",
        help="Add one collected model response.",
    )
    add_parser.add_argument(
        "case_id",
        help="Canonical case identifier.",
    )
    add_parser.add_argument(
        "--response-json",
        help="Response JSON supplied directly.",
    )
    add_parser.add_argument(
        "--response-file",
        type=Path,
        help="File containing one response JSON object.",
    )
    add_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Intentionally replace an existing response.",
    )

    paste_parser = subparsers.add_parser(
        "paste",
        help=(
            "Read one response JSON object from the Windows "
            "clipboard and save it."
        ),
    )
    paste_parser.add_argument(
        "case_id",
        help="Canonical case identifier.",
    )
    paste_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Intentionally replace an existing response.",
    )
    paste_parser.add_argument(
        "--show-next",
        action="store_true",
        help="Display the next missing prompt after saving.",
    )
    paste_parser.add_argument(
        "--open-next",
        action="store_true",
        help="Open the next missing prompt after saving.",
    )


    subparsers.add_parser(
        "validate",
        help="Validate the complete response collection.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    pilot_directory = arguments.pilot.resolve()
    responses_path = pilot_directory / "responses.json"

    records = load_records(responses_path)

    if arguments.command == "status":
        show_progress(records)
        return 0

    if arguments.command == "next":
        record = next_missing_record(records)

        if record is None:
            print("[PASS] No responses are missing")
            return 0

        case_id = record["case_id"]

        show_prompt(
            pilot_directory=pilot_directory,
            case_id=case_id,
        )

        if arguments.open:
            import os
            import shutil
            import subprocess

            prompt_path = (
                pilot_directory
                / "text"
                / f"{case_id}.txt"
            )

            code_command = (
                shutil.which("code")
                or shutil.which("code.cmd")
            )

            if code_command:
                subprocess.run(
                    [code_command, str(prompt_path)],
                    check=False,
                )
            elif os.name == "nt":
                os.startfile(prompt_path)  # type: ignore[attr-defined]
            else:
                print(
                    "[WARN] Editor launcher was not found; "
                    f"open manually: {prompt_path}"
                )

        return 0

    if arguments.command == "show":
        find_record(records, arguments.case_id)
        show_prompt(
            pilot_directory=pilot_directory,
            case_id=arguments.case_id,
        )
        return 0

    if arguments.command == "add":
        response = parse_response_argument(
            response_json=arguments.response_json,
            response_file=arguments.response_file,
        )

        updated = add_response(
            records=records,
            case_id=arguments.case_id,
            response=response,
            overwrite=arguments.overwrite,
        )

        write_json_atomic(
            responses_path,
            records,
        )

        print(
            f"[PASS] Response saved for "
            f"{updated['case_id']}"
        )
        print(
            f"Prediction: {response['prediction']}"
        )
        print(
            f"Confidence: {response['confidence']}"
        )

        remaining = sum(
            not is_complete(record)
            for record in records
        )

        print(f"Remaining:  {remaining}")

        return 0

    if arguments.command == "paste":
        response = read_clipboard_response()

        updated = add_response(
            records=records,
            case_id=arguments.case_id,
            response=response,
            overwrite=arguments.overwrite,
        )

        write_json_atomic(
            responses_path,
            records,
        )

        print(
            f"[PASS] Clipboard response saved for "
            f"{updated['case_id']}"
        )
        print(f"Prediction: {response['prediction']}")
        print(f"Confidence: {response['confidence']}")

        remaining = sum(
            not is_complete(record)
            for record in records
        )

        print(f"Remaining:  {remaining}")

        next_record = next_missing_record(records)

        if next_record is None:
            print()
            print("[PASS] All pilot responses have been collected")
            return 0

        if arguments.show_next or arguments.open_next:
            next_case_id = next_record["case_id"]

            print()
            show_prompt(
                pilot_directory=pilot_directory,
                case_id=next_case_id,
            )

            if arguments.open_next:
                import os
                import shutil
                import subprocess

                prompt_path = (
                    pilot_directory
                    / "text"
                    / f"{next_case_id}.txt"
                )

                code_command = (
                    shutil.which("code")
                    or shutil.which("code.cmd")
                )

                if code_command:
                    subprocess.run(
                        [code_command, str(prompt_path)],
                        check=False,
                    )
                elif os.name == "nt":
                    os.startfile(  # type: ignore[attr-defined]
                        prompt_path
                    )
                else:
                    print(
                        "[WARN] Editor launcher was not found; "
                        f"open manually: {prompt_path}"
                    )

        return 0


    if arguments.command == "validate":
        validate_collection(records)
        return 0

    parser.error(
        f"Unsupported command: {arguments.command}"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())