from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import csv
import json


@dataclass(frozen=True)
class PluginRecord:
    plugin_id: str
    module: str
    class_name: str
    version: str
    status: str
    source_type: str
    description: str

    @property
    def active(self) -> bool:
        return self.status.casefold() == "active"


def _validate_unique(records: Iterable[PluginRecord]) -> list[PluginRecord]:
    result = list(records)
    identifiers = [record.plugin_id for record in result]
    duplicates = sorted(
        identifier
        for identifier in set(identifiers)
        if identifiers.count(identifier) > 1
    )
    if duplicates:
        raise ValueError(f"Duplicate plugin IDs: {duplicates}")
    return result


def load_csv(path: Path) -> list[PluginRecord]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        records = [
            PluginRecord(
                plugin_id=row["plugin_id"].strip(),
                module=row["module"].strip(),
                class_name=row["class_name"].strip(),
                version=row["version"].strip(),
                status=row["status"].strip(),
                source_type=row["source_type"].strip(),
                description=row["description"].strip(),
            )
            for row in reader
        ]
    return _validate_unique(records)


def load_json(path: Path) -> list[PluginRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = [
        PluginRecord(
            plugin_id=item["plugin_id"],
            module=item["module"],
            class_name=item["class_name"],
            version=item["version"],
            status=item["status"],
            source_type=item["source_type"],
            description=item["description"],
        )
        for item in payload["plugins"]
    ]
    return _validate_unique(records)
