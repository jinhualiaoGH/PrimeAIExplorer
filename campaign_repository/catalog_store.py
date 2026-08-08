from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Iterable

from kernel.exceptions import ValidationError
from experimental_campaign.identity import sha256_json

from .catalog_contracts import ScientificReleaseCatalogRecord


def _canonical_json_bytes(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


class ScientificReleaseCatalog:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.records_root = self.root / "records"
        self.index_path = self.root / "catalog.json"

    def initialize(self) -> None:
        self.records_root.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self._write_replaceable(
                self.index_path,
                _canonical_json_bytes(
                    {
                        "schema_version": "i7.0",
                        "release_ids": [],
                    }
                ),
            )

    def register(
        self,
        record: ScientificReleaseCatalogRecord,
    ) -> bool:
        if not isinstance(record, ScientificReleaseCatalogRecord):
            raise ValidationError(
                "record must be ScientificReleaseCatalogRecord."
            )

        self.initialize()
        path = self.records_root / f"{record.release_id}.json"

        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing.get("record_sha256") == record.record_sha256:
                return False
            raise ValidationError(
                f"release ID conflict: {record.release_id}"
            )

        self._write_immutable(
            path,
            _canonical_json_bytes(record.to_dict()),
        )

        ids = list(self._load_index()["release_ids"])
        ids.append(record.release_id)
        ids = sorted(set(ids))
        self._write_replaceable(
            self.index_path,
            _canonical_json_bytes(
                {
                    "schema_version": "i7.0",
                    "release_ids": ids,
                }
            ),
        )
        return True

    def get(
        self,
        release_id: str,
    ) -> dict:
        path = self.records_root / f"{release_id}.json"
        if not path.is_file():
            raise KeyError(release_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def contains(
        self,
        release_id: str,
    ) -> bool:
        return (self.records_root / f"{release_id}.json").is_file()

    def list_records(self) -> tuple[dict, ...]:
        self.initialize()
        records = [
            self.get(release_id)
            for release_id in self._load_index()["release_ids"]
        ]
        return tuple(
            sorted(records, key=lambda item: item["release_id"])
        )

    def catalog_sha256(self) -> str:
        return sha256_json(
            {
                "schema_version": "i7.0",
                "records": list(self.list_records()),
            }
        )

    def _load_index(self) -> dict:
        self.initialize()
        return json.loads(
            self.index_path.read_text(encoding="utf-8")
        )

    @staticmethod
    def _write_immutable(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() == data:
                return
            raise ValidationError(
                f"immutable catalog record conflict: {path}"
            )

        fd, temp_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=str(path.parent),
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    @staticmethod
    def _write_replaceable(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=str(path.parent),
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
