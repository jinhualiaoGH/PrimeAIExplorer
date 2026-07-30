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


def load_truth(path: Path) -> dict[str, int]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        required = {"case_id", "actual_gap"}
        if not required.issubset(rows.fieldnames or []):
            raise ValueError(f"truth CSV requires columns: {sorted(required)}")
        return {row["case_id"].strip(): int(row["actual_gap"]) for row in rows}


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
    patterns = ("*.response.json", "*_response.json")
    found = {p.resolve() for pattern in patterns for p in folder.rglob(pattern)}
    return sorted(found)


def case_id_from_path(path: Path) -> str:
    match = CASE_RE.search(path.name)
    if not match:
        raise ValueError(f"Cannot derive CASE-Wxxx-nnnn identifier from {path.name}")
    return match.group(0).upper()


def load_records(folder: Path, truth_path: Path) -> list[ResponseRecord]:
    truth = load_truth(truth_path)
    response_paths = discover_responses(folder)
    if not response_paths:
        raise ValueError(f"No *.response.json or *_response.json files found under {folder}")
    records = []
    for path in response_paths:
        case_id = case_id_from_path(path)
        if case_id not in truth:
            raise ValueError(f"{path}: {case_id} is absent from truth CSV")
        with path.open("r", encoding="utf-8-sig") as stream:
            payload = json.load(stream)
        prediction, confidence, explanation = _validate_payload(payload, path)
        match = CASE_RE.search(case_id)
        actual = truth[case_id]
        records.append(ResponseRecord(
            case_id=case_id,
            window=int(match.group("window")) if match else None,
            prediction=prediction,
            confidence=confidence,
            explanation=explanation,
            actual_gap=actual,
            response_path=str(path),
            response_sha256=sha256_file(path),
            correct=prediction == actual,
        ))
    return records
