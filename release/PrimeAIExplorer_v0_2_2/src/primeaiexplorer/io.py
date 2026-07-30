from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

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
    """Load a canonical cases.csv file and index it by case_id."""
    if not path.is_file():
        raise FileNotFoundError(f"Dataset CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        fields = set(rows.fieldnames or [])
        if "case_id" not in fields:
            raise ValueError("dataset CSV requires column: case_id")
        truth_field = (
            "ground_truth" if "ground_truth" in fields
            else "actual_gap" if "actual_gap" in fields
            else None
        )
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
                ground_truth=_parse_positive_int(
                    row.get(truth_field), field=truth_field, row_number=row_number
                ),
                window_size=window_size,
                pair_id=(row.get("pair_id") or "").strip() or None,
            )

    if not dataset:
        raise ValueError(f"Dataset CSV contains no cases: {path}")
    return dataset


def _validate_payload(payload: Any, source: str) -> tuple[int, int, str]:
    if not isinstance(payload, dict):
        raise ValueError(f"{source}: response must be a JSON object")
    expected = {"prediction", "confidence", "explanation"}
    missing = expected - payload.keys()
    if missing:
        raise ValueError(f"{source}: missing fields {sorted(missing)}")
    prediction = payload["prediction"]
    confidence = payload["confidence"]
    explanation = payload["explanation"]
    if isinstance(prediction, bool) or not isinstance(prediction, int) or prediction < 1:
        raise ValueError(f"{source}: prediction must be a positive integer")
    if prediction != 1 and prediction % 2:
        raise ValueError(f"{source}: prime gaps after the initial gap should be even")
    if isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100:
        raise ValueError(f"{source}: confidence must be an integer from 0 to 100")
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError(f"{source}: explanation must be non-empty text")
    return prediction, confidence, explanation.strip()


def case_id_from_path(path: Path) -> str:
    match = CASE_RE.search(path.name)
    if not match:
        raise ValueError(f"Cannot derive CASE-Wxxx-nnnn identifier from {path.name}")
    return match.group(0).upper()


def _normalize_case_id(value: Any, source: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{source}: case_id must be text")
    match = CASE_RE.search(value)
    if not match:
        raise ValueError(f"{source}: invalid or missing CASE-Wxxx-nnnn case_id")
    return match.group(0).upper()


def _decode_json_text(value: str, source: str) -> Any:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source}: embedded response text is not valid JSON") from exc


def _extract_response_payload(entry: dict[str, Any], source: str) -> dict[str, Any]:
    if {"prediction", "confidence", "explanation"}.issubset(entry):
        return entry

    for key in ("response", "parsed_response", "result", "output", "answer", "payload"):
        if key not in entry:
            continue
        value = entry[key]
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            decoded = _decode_json_text(value, source)
            if isinstance(decoded, dict):
                return decoded

    raise ValueError(f"{source}: cannot locate prediction/confidence/explanation payload")


def _iter_aggregate_entries(payload: Any, path: Path) -> Iterable[tuple[str, dict[str, Any], str]]:
    """Yield (case_id, response payload, source label) from common aggregate schemas."""
    source = str(path)

    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        for key in ("responses", "records", "items", "results"):
            if isinstance(payload.get(key), list):
                entries = payload[key]
                break
            if isinstance(payload.get(key), dict):
                mapping = payload[key]
                for case_key, value in mapping.items():
                    item_source = f"{source}:{case_key}"
                    if not isinstance(value, dict):
                        raise ValueError(f"{item_source}: aggregate response entry must be an object")
                    case_id = _normalize_case_id(value.get("case_id", case_key), item_source)
                    yield case_id, _extract_response_payload(value, item_source), item_source
                return
        else:
            case_keys = [key for key in payload if CASE_RE.search(str(key))]
            if case_keys:
                for case_key in case_keys:
                    value = payload[case_key]
                    item_source = f"{source}:{case_key}"
                    if not isinstance(value, dict):
                        raise ValueError(f"{item_source}: aggregate response entry must be an object")
                    case_id = _normalize_case_id(value.get("case_id", case_key), item_source)
                    yield case_id, _extract_response_payload(value, item_source), item_source
                return
            if "case_id" in payload:
                entries = [payload]
            else:
                raise ValueError(
                    f"{source}: unsupported aggregate schema; expected a list, a responses/records/items/results collection, or CASE-ID keys"
                )
    else:
        raise ValueError(f"{source}: aggregate responses JSON must be an object or array")

    for index, value in enumerate(entries, start=1):
        item_source = f"{source}#entry-{index}"
        if not isinstance(value, dict):
            raise ValueError(f"{item_source}: aggregate response entry must be an object")
        raw_case_id = value.get("case_id") or value.get("id") or value.get("case") or value.get("prompt_id")
        case_id = _normalize_case_id(raw_case_id, item_source)
        yield case_id, _extract_response_payload(value, item_source), item_source


def _individual_response_paths(folder: Path) -> list[Path]:
    patterns = ("*.response.json", "*_response.json")
    return sorted({p.resolve() for pattern in patterns for p in folder.rglob(pattern)})


def discover_response_sources(path: Path) -> tuple[list[Path], list[Path]]:
    """Return aggregate files and individual response files.

    If *path* is a JSON file it is treated as an aggregate source. If it is a
    directory, every responses.json is loaded plus legacy individual response
    files. current_response.json is intentionally ignored because it is a
    mutable collection scratch file rather than the canonical response ledger.
    """
    if path.is_file():
        if path.suffix.lower() != ".json":
            raise ValueError(f"Response source must be JSON: {path}")
        return [path.resolve()], []
    if not path.is_dir():
        raise FileNotFoundError(f"Response source not found: {path}")
    aggregates = sorted(p.resolve() for p in path.rglob("responses.json"))
    individuals = _individual_response_paths(path)
    return aggregates, individuals


def load_records(response_source: Path, dataset_path: Path) -> list[ResponseRecord]:
    dataset = load_dataset(dataset_path)
    aggregate_paths, individual_paths = discover_response_sources(response_source)
    if not aggregate_paths and not individual_paths:
        raise ValueError(
            f"No responses.json, *.response.json, or *_response.json found under {response_source}"
        )

    records: list[ResponseRecord] = []
    seen_case_ids: dict[str, str] = {}

    def append_record(case_id: str, payload: dict[str, Any], source_label: str, source_path: Path) -> None:
        if case_id in seen_case_ids:
            raise ValueError(
                f"Duplicate response for {case_id}: {source_label}; first seen at {seen_case_ids[case_id]}"
            )
        if case_id not in dataset:
            raise ValueError(f"{source_label}: {case_id} is absent from dataset CSV")
        prediction, confidence, explanation = _validate_payload(payload, source_label)
        case = dataset[case_id]
        seen_case_ids[case_id] = source_label
        records.append(
            ResponseRecord(
                case_id=case_id,
                window=case.window_size,
                prediction=prediction,
                confidence=confidence,
                explanation=explanation,
                actual_gap=case.ground_truth,
                response_path=source_label,
                response_sha256=sha256_file(source_path),
                correct=prediction == case.ground_truth,
            )
        )

    for path in aggregate_paths:
        with path.open("r", encoding="utf-8-sig") as stream:
            payload = json.load(stream)
        for case_id, response_payload, source_label in _iter_aggregate_entries(payload, path):
            append_record(case_id, response_payload, source_label, path)

    for path in individual_paths:
        case_id = case_id_from_path(path)
        with path.open("r", encoding="utf-8-sig") as stream:
            payload = json.load(stream)
        append_record(case_id, payload, str(path), path)

    return sorted(records, key=lambda row: (row.window if row.window is not None else -1, row.case_id))
