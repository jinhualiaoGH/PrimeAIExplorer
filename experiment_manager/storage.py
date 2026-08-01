"""Atomic and append-only persistence primitives."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable, Mapping


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a value deterministically for hashing and persistence."""

    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return text.encode("utf-8")


def atomic_write_json(path: Path, value: Any) -> None:
    """Atomically replace a JSON document in the destination directory."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)

        json.dump(
            value,
            handle,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())

    try:
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def read_json(path: Path) -> dict[str, Any]:
    """Read one JSON object."""

    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}.")

    return value


def append_jsonl(path: Path, value: Mapping[str, Any]) -> None:
    """Append one durable JSON record."""

    path.parent.mkdir(parents=True, exist_ok=True)

    line = canonical_json_bytes(dict(value)) + b"\n"

    with path.open("ab") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    """Yield all valid JSONL records."""

    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()

            if not line:
                continue

            value = json.loads(line)

            if not isinstance(value, dict):
                raise ValueError(
                    f"Expected a JSON object at {path}:{line_number}."
                )

            yield value
