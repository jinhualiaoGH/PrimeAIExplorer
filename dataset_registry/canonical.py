"""Canonical JSON and deterministic dataset identifiers."""

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


def dataset_id_from_document(document: Mapping[str, Any]) -> str:
    material = dict(document)
    material.pop("dataset_id", None)
    digest = hashlib.sha256(canonical_json_bytes(material)).hexdigest()
    return f"DS-{digest[:16].upper()}"
