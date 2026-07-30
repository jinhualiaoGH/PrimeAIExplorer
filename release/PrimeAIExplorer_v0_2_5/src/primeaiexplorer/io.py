from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

CASE_RE = re.compile(r"CASE-W(?P<window>\d+)-(?P<number>\d+)", re.IGNORECASE)

IGNORED_RESPONSE_FILENAMES = {
    "current_response.json",
    "pilot_manifest.json",
}


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
    collection_sha256: str
    entry_sha256: str
    # Backward-compatible alias. In v0.2.3 this is the per-entry hash.
    response_sha256: str
    correct: bool


@dataclass(frozen=True)
class LedgerStatus:
    ledger_entries: int
    completed_entries: int
    pending_entries: int
    collection_count: int


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


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
    text = value.strip().lstrip("\ufeff")
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


def parse_json_documents(path: Path) -> list[Any]:
    """Parse one standard JSON document or multiple concatenated JSON documents.

    The file is decoded with ``utf-8-sig`` so an optional UTF-8 BOM is removed.
    The raw decoder then accepts ordinary JSON, NDJSON, and consecutive objects
    separated only by whitespace.
    """
    text = path.read_text(encoding="utf-8-sig")
    decoder = json.JSONDecoder()
    documents: list[Any] = []
    position = 0

    while position < len(text):
        while position < len(text) and text[position].isspace():
            position += 1
        if position >= len(text):
            break
        try:
            value, next_position = decoder.raw_decode(text, position)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{path}: invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}"
            ) from exc
        documents.append(value)
        position = next_position

    if not documents:
        raise ValueError(f"{path}: response file contains no JSON documents")
    return documents


def _iter_standard_aggregate_entries(payload: Any, path: Path) -> Iterator[tuple[str | None, dict[str, Any], str]]:
    """Yield optional case_id, response payload, and source from one JSON value."""
    source = str(path)

    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        if {"prediction", "confidence", "explanation"}.issubset(payload):
            raw_case_id = payload.get("case_id") or payload.get("id") or payload.get("case") or payload.get("prompt_id")
            case_id = _normalize_case_id(raw_case_id, source) if raw_case_id is not None else None
            yield case_id, _extract_response_payload(payload, source), source
            return

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
                    f"{source}: unsupported aggregate schema; expected response objects, a list, "
                    "a responses/records/items/results collection, or CASE-ID keys"
                )
    else:
        raise ValueError(f"{source}: aggregate responses JSON must be an object or array")

    for index, value in enumerate(entries, start=1):
        item_source = f"{source}#entry-{index}"
        if not isinstance(value, dict):
            raise ValueError(f"{item_source}: aggregate response entry must be an object")
        # Preallocated pilot ledgers intentionally use response=null for pending cases.
        if "response" in value and value["response"] is None:
            continue
        raw_case_id = value.get("case_id") or value.get("id") or value.get("case") or value.get("prompt_id")
        case_id = _normalize_case_id(raw_case_id, item_source) if raw_case_id is not None else None
        yield case_id, _extract_response_payload(value, item_source), item_source


def _prompt_sort_key(path: Path) -> tuple[int, int, str]:
    match = CASE_RE.search(path.name)
    if not match:
        return (10**9, 10**9, path.name.lower())
    return (int(match.group("number")), int(match.group("window")), path.name.lower())


def discover_prompt_case_ids(response_source: Path, prompts: Path | None = None) -> list[str]:
    """Discover deterministic case order from CASE-*.txt prompt files.

    Ordering is pair number first and window size second. This yields W004,
    W008, W016, W032, W064 within each paired target and works for prompt files
    in either the pilot root or nested ``text`` directories.
    """
    if prompts is not None:
        root = prompts
    elif response_source.is_dir():
        root = response_source
    else:
        root = response_source.parent

    if not root.exists():
        return []
    paths = sorted(
        (p for p in root.rglob("CASE-*.txt") if CASE_RE.search(p.name)),
        key=_prompt_sort_key,
    )
    return [case_id_from_path(path) for path in paths]


def _individual_response_paths(folder: Path) -> list[Path]:
    patterns = ("*.response.json", "*_response.json")
    return sorted(
        {
            p.resolve()
            for pattern in patterns
            for p in folder.rglob(pattern)
            if p.name.lower() not in IGNORED_RESPONSE_FILENAMES
        }
    )


def discover_response_sources(path: Path) -> tuple[list[Path], list[Path]]:
    """Return aggregate files and individual response files."""
    if path.is_file():
        if path.suffix.lower() != ".json":
            raise ValueError(f"Response source must be JSON: {path}")
        return [path.resolve()], []
    if not path.is_dir():
        raise FileNotFoundError(f"Response source not found: {path}")
    aggregates = sorted(p.resolve() for p in path.rglob("responses.json"))
    individuals = _individual_response_paths(path)
    return aggregates, individuals


def _count_document_entries(document: Any) -> tuple[int, int]:
    """Return (ledger entries, pending entries) for one parsed JSON document."""
    if isinstance(document, list):
        entries = document
    elif isinstance(document, dict):
        for key in ("responses", "records", "items", "results"):
            value = document.get(key)
            if isinstance(value, list):
                entries = value
                break
            if isinstance(value, dict):
                entries = list(value.values())
                break
        else:
            case_keys = [key for key in document if CASE_RE.search(str(key))]
            entries = [document[key] for key in case_keys] if case_keys else [document]
    else:
        entries = [document]
    pending = sum(1 for entry in entries if isinstance(entry, dict) and "response" in entry and entry["response"] is None)
    return len(entries), pending


def inspect_ledger_status(response_source: Path) -> LedgerStatus:
    aggregate_paths, individual_paths = discover_response_sources(response_source)
    ledger_entries = 0
    pending_entries = 0
    for path in aggregate_paths:
        for document in parse_json_documents(path):
            count, pending = _count_document_entries(document)
            ledger_entries += count
            pending_entries += pending
    ledger_entries += len(individual_paths)
    completed_entries = ledger_entries - pending_entries
    return LedgerStatus(
        ledger_entries=ledger_entries,
        completed_entries=completed_entries,
        pending_entries=pending_entries,
        collection_count=len(aggregate_paths) + len(individual_paths),
    )



def locate_canonical_ledger(response_source: Path) -> Path:
    """Locate the single canonical ``responses.json`` ledger."""
    if response_source.is_file():
        if response_source.name.lower() != "responses.json":
            raise ValueError(
                "Collection requires the canonical responses.json ledger, "
                f"not {response_source.name}"
            )
        return response_source.resolve()
    if not response_source.is_dir():
        raise FileNotFoundError(f"Pilot directory not found: {response_source}")
    candidates = sorted(response_source.rglob("responses.json"))
    if not candidates:
        raise FileNotFoundError(f"No responses.json ledger found under {response_source}")
    if len(candidates) != 1:
        joined = ", ".join(str(path) for path in candidates)
        raise ValueError(f"Collection requires exactly one responses.json ledger; found: {joined}")
    return candidates[0].resolve()


def _ledger_entries_container(document: Any, source: Path) -> list[dict[str, Any]]:
    """Return the mutable entry list from a supported preallocated ledger."""
    if isinstance(document, list):
        entries = document
    elif isinstance(document, dict):
        entries = None
        for key in ("responses", "records", "items", "results"):
            if isinstance(document.get(key), list):
                entries = document[key]
                break
        if entries is None:
            raise ValueError(
                f"{source}: collect requires a JSON array or an object containing a response list"
            )
    else:
        raise ValueError(f"{source}: collect requires a JSON array or object ledger")
    if not all(isinstance(entry, dict) for entry in entries):
        raise ValueError(f"{source}: every ledger entry must be a JSON object")
    return entries


def commit_pilot_response(
    response_source: Path,
    dataset_path: Path,
    payload: dict[str, Any],
    *,
    case_id: str | None = None,
    model: str = "unknown-model",
    collection_mode: str = "manual_chat",
    dry_run: bool = False,
) -> tuple[str, Path, Path | None]:
    """Validate and atomically commit one response into a partial pilot ledger.

    Returns ``(case_id, ledger_path, backup_path)``.  The first pending entry is
    selected when ``case_id`` is omitted.  Existing completed responses are
    never overwritten.
    """
    from datetime import datetime, timezone

    ledger_path = locate_canonical_ledger(response_source)
    dataset = load_dataset(dataset_path)
    document = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    entries = _ledger_entries_container(document, ledger_path)

    selected: dict[str, Any] | None = None
    selected_case_id: str | None = None
    requested = case_id.upper() if case_id else None

    for entry in entries:
        raw_case = entry.get("case_id") or entry.get("id") or entry.get("case")
        if raw_case is None:
            continue
        entry_case_id = _normalize_case_id(raw_case, str(ledger_path))
        if requested is not None and entry_case_id != requested:
            continue
        if entry.get("response") is not None:
            if requested is not None:
                raise ValueError(f"{entry_case_id} already has a committed response")
            continue
        selected = entry
        selected_case_id = entry_case_id
        break

    if selected is None or selected_case_id is None:
        if requested:
            raise ValueError(f"No pending ledger entry found for {requested}")
        raise ValueError("Pilot is complete; no pending ledger entry remains")
    if selected_case_id not in dataset:
        raise ValueError(f"{selected_case_id} is absent from dataset CSV")

    prediction, confidence, explanation = _validate_payload(payload, selected_case_id)
    normalized = {
        "prediction": prediction,
        "confidence": confidence,
        "explanation": explanation,
    }
    selected["response"] = normalized
    selected["collected_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    selected["collection_mode"] = collection_mode
    selected["model"] = model

    if dry_run:
        return selected_case_id, ledger_path, None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = ledger_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"responses.before_collect_{timestamp}.json"
    counter = 1
    while backup_path.exists():
        backup_path = backup_dir / f"responses.before_collect_{timestamp}_{counter}.json"
        counter += 1
    backup_path.write_bytes(ledger_path.read_bytes())

    temporary = ledger_path.with_name(ledger_path.name + ".tmp")
    temporary.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(ledger_path)
    return selected_case_id, ledger_path, backup_path


def load_records(
    response_source: Path,
    dataset_path: Path,
    prompts: Path | None = None,
) -> list[ResponseRecord]:
    dataset = load_dataset(dataset_path)
    aggregate_paths, individual_paths = discover_response_sources(response_source)
    if not aggregate_paths and not individual_paths:
        raise ValueError(
            f"No responses.json, *.response.json, or *_response.json found under {response_source}"
        )

    records: list[ResponseRecord] = []
    seen_case_ids: dict[str, str] = {}
    prompt_case_ids = discover_prompt_case_ids(response_source, prompts)
    prompt_cursor = 0

    def next_prompt_case_id(source_label: str) -> str:
        nonlocal prompt_cursor
        if prompt_cursor >= len(prompt_case_ids):
            raise ValueError(
                f"{source_label}: response has no case_id and no unused CASE-*.txt prompt is available. "
                "Supply --prompts with the pilot prompt directory."
            )
        case_id = prompt_case_ids[prompt_cursor]
        prompt_cursor += 1
        return case_id

    def append_record(
        case_id: str,
        payload: dict[str, Any],
        source_label: str,
        source_path: Path,
        collection_hash: str,
    ) -> None:
        if case_id in seen_case_ids:
            raise ValueError(
                f"Duplicate response for {case_id}: {source_label}; first seen at {seen_case_ids[case_id]}"
            )
        if case_id not in dataset:
            raise ValueError(f"{source_label}: {case_id} is absent from dataset CSV")
        prediction, confidence, explanation = _validate_payload(payload, source_label)
        case = dataset[case_id]
        normalized_entry = {
            "case_id": case_id,
            "prediction": prediction,
            "confidence": confidence,
            "explanation": explanation,
        }
        entry_hash = sha256_json(normalized_entry)
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
                collection_sha256=collection_hash,
                entry_sha256=entry_hash,
                response_sha256=entry_hash,
                correct=prediction == case.ground_truth,
            )
        )

    for path in aggregate_paths:
        collection_hash = sha256_file(path)
        documents = parse_json_documents(path)
        aggregate_entries: list[tuple[str | None, dict[str, Any], str]] = []
        for document_index, document in enumerate(documents, start=1):
            for case_id, payload, source_label in _iter_standard_aggregate_entries(document, path):
                if len(documents) > 1:
                    source_label = f"{path}#document-{document_index}"
                aggregate_entries.append((case_id, payload, source_label))

        for entry_index, (case_id, response_payload, source_label) in enumerate(aggregate_entries, start=1):
            effective_source = source_label
            if len(aggregate_entries) > 1 and "#" not in effective_source:
                effective_source = f"{path}#entry-{entry_index}"
            resolved_case_id = case_id or next_prompt_case_id(effective_source)
            append_record(resolved_case_id, response_payload, effective_source, path, collection_hash)

    for path in individual_paths:
        case_id = case_id_from_path(path)
        documents = parse_json_documents(path)
        if len(documents) != 1:
            raise ValueError(f"{path}: individual response file must contain exactly one JSON document")
        payload = documents[0]
        if not isinstance(payload, dict):
            raise ValueError(f"{path}: individual response must be a JSON object")
        append_record(case_id, payload, str(path), path, sha256_file(path))

    return sorted(records, key=lambda row: (row.window if row.window is not None else -1, row.case_id))
