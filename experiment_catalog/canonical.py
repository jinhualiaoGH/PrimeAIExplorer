"""Canonical snapshot hashing and deterministic record identifiers."""

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


def snapshot_sha256(snapshot: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(snapshot)).hexdigest()


def record_id_from_snapshot(snapshot: Mapping[str, Any]) -> str:
    digest = snapshot_sha256(snapshot)
    return f"XR-{digest[:16].upper()}"
