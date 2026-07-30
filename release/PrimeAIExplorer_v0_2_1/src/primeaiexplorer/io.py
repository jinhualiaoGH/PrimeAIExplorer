from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CASE_RE = re.compile(r"CASE-W(?P<window>\d+)-(?P<number>\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class DatasetCase:
    case_id: str
    ground_truth: int
    window_size: int | None
    pair_id: str | None


@dataclass(frozen=True)
class ResponseRecord:
    case_id: str
    window: int | None
    prediction: int
    confidence: int
    explanation: str
    actual_gap: int
    response_path: str
    response_sha256: str
    correct: bool


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _parse_positive_int(value: str | None, *, field: str, row_number: int) -> int:
    try:
        parsed = int((value or "").strip())
    except ValueError as exc:
        raise ValueError(f"dataset row {row_number}: {field} must be an integer") from exc
    if parsed < 1:
        raise ValueError(f"dataset row {row_number}: {field} must be positive")
    return parsed


def load_dataset(path: Path) -> dict[str, DatasetCase]:
    """Load the canonical EXP dataset CSV and index it by case_id.

    The canonical generator writes ``ground_truth``. ``actual_gap`` is accepted
    as a compatibility alias for older exports.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Dataset CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        fields = set(rows.fieldnames or [])
        if "case_id" not in fields:
            raise ValueError("dataset CSV requires column: case_id")
        truth_field = "ground_truth" if "ground_truth" in fields else "actual_gap" if "actual_gap" in fields else None
        if truth_field is None:
            raise ValueError("dataset CSV requires column: ground_truth")

        dataset: dict[str, DatasetCase] = {}
        for row_number, row in enumerate(rows, start=2):
            case_id = (row.get("case_id") or "").strip().upper()
            if not case_id:
                raise ValueError(f"dataset row {row_number}: case_id is empty")
            if case_id in dataset:
                raise ValueError(f"dataset row {row_number}: duplicate case_id {case_id}")

            match = CASE_RE.fullmatch(case_id)
            inferred_window = int(match.group("window")) if match else None
            raw_window = (row.get("window_size") or "").strip()
            window_size = int(raw_window) if raw_window else inferred_window
            if inferred_window is not None and window_size != inferred_window:
                raise ValueError(
                    f"dataset row {row_number}: window_size {window_size} conflicts with {case_id}"
                )

            dataset[case_id] = DatasetCase(
                case_id=case_id,
                ground_truth=_parse_positive_int(row.get(truth_field), field=truth_field, row_number=row_number),
                window_size=window_size,
                pair_id=(row.get("pair_id") or "").strip() or None,
            )

    if not dataset:
        raise ValueError(f"Dataset CSV contains no cases: {path}")
    return dataset


def _validate_payload(payload: Any, path: Path) -> tuple[int, int, str]:
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: response must be a JSON object")
    expected = {"prediction", "confidence", "explanation"}
    missing = expected - payload.keys()
    if missing:
        raise ValueError(f"{path}: missing fields {sorted(missing)}")
    prediction = payload["prediction"]
    confidence = payload["confidence"]
    explanation = payload["explanation"]
    if isinstance(prediction, bool) or not isinstance(prediction, int) or prediction < 1:
        raise ValueError(f"{path}: prediction must be a positive integer")
    if prediction != 1 and prediction % 2:
        raise ValueError(f"{path}: prime gaps after the initial gap should be even")
    if isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100:
        raise ValueError(f"{path}: confidence must be an integer from 0 to 100")
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError(f"{path}: explanation must be non-empty text")
    return prediction, confidence, explanation.strip()


def discover_responses(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise FileNotFoundError(f"Response directory not found: {folder}")
    patterns = ("*.response.json", "*_response.json")
    found = {p.resolve() for pattern in patterns for p in folder.rglob(pattern)}
    return sorted(found)


def case_id_from_path(path: Path) -> str:
    match = CASE_RE.search(path.name)
    if not match:
        raise ValueError(f"Cannot derive CASE-Wxxx-nnnn identifier from {path.name}")
    return match.group(0).upper()


def load_records(folder: Path, dataset_path: Path) -> list[ResponseRecord]:
    dataset = load_dataset(dataset_path)
    response_paths = discover_responses(folder)
    if not response_paths:
        raise ValueError(f"No *.response.json or *_response.json files found under {folder}")

    records: list[ResponseRecord] = []
    seen_case_ids: set[str] = set()
    for path in response_paths:
        case_id = case_id_from_path(path)
        if case_id in seen_case_ids:
            raise ValueError(f"Duplicate response for {case_id}: {path}")
        seen_case_ids.add(case_id)
        if case_id not in dataset:
            raise ValueError(f"{path}: {case_id} is absent from dataset CSV")

        with path.open("r", encoding="utf-8-sig") as stream:
            payload = json.load(stream)
        prediction, confidence, explanation = _validate_payload(payload, path)
        case = dataset[case_id]
        records.append(
            ResponseRecord(
                case_id=case_id,
                window=case.window_size,
                prediction=prediction,
                confidence=confidence,
                explanation=explanation,
                actual_gap=case.ground_truth,
                response_path=str(path),
                response_sha256=sha256_file(path),
                correct=prediction == case.ground_truth,
            )
        )
    return records
