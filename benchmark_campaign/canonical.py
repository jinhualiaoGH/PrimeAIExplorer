"""Canonical JSON and deterministic campaign identifiers."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def deterministic_id(
    prefix: str,
    document: Mapping[str, Any],
    *,
    length: int = 16,
) -> str:
    digest = hashlib.sha256(canonical_json_bytes(document)).hexdigest()
    return f"{prefix}-{digest[:length].upper()}"
