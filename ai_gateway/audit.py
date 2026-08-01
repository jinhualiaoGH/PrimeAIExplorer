from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Any


_SECRET_MARKERS = ("key", "token", "secret", "password", "authorization")


def redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if any(marker in key.lower() for marker in _SECRET_MARKERS):
            result[key] = "[REDACTED]"
        elif isinstance(item, Mapping):
            result[key] = redact_mapping(item)
        else:
            result[key] = item
    return result


class JsonlAuditSink:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write(self, event: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(
                    redact_mapping(event),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n"
            )
