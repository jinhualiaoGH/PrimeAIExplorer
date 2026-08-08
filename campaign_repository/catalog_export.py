from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experimental_campaign.identity import sha256_json

from .catalog_store import ScientificReleaseCatalog


def export_catalog_snapshot(
    catalog: ScientificReleaseCatalog,
    destination: str | Path,
) -> dict[str, Any]:
    records = list(catalog.list_records())

    payload = {
        "schema_version": "i7.0",
        "catalog_sha256": catalog.catalog_sha256(),
        "record_count": len(records),
        "records": records,
    }

    payload["snapshot_sha256"] = sha256_json(payload)

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return payload
