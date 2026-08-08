from __future__ import annotations

from typing import Any, Mapping

from .identity import canonical_json, sha256_json


def content_sha256(value: Any) -> str:
    """Return the canonical SHA-256 identity for registry content."""
    return sha256_json(value)


def registry_entry_identity(
    *,
    kind: str,
    entry_id: str,
    version: str,
    payload: Mapping[str, Any],
) -> str:
    return content_sha256(
        {
            "schema_version": "h2.0",
            "kind": kind,
            "entry_id": entry_id,
            "version": version,
            "payload": dict(payload),
        }
    )


__all__ = [
    "canonical_json",
    "content_sha256",
    "registry_entry_identity",
]
