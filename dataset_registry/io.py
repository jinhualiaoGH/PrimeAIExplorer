"""Dataset manifest serialization and artifact hashing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .models import (
    DatasetArtifact,
    DatasetManifest,
    DatasetSplit,
    ProvenanceRecord,
)


def sha256_file(path: str | Path, *, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def artifact_from_file(
    root: str | Path,
    path: str | Path,
    *,
    media_type: str = "application/octet-stream",
    record_count: int | None = None,
) -> DatasetArtifact:
    root_path = Path(root).resolve()
    source = Path(path).resolve()
    relative = source.relative_to(root_path).as_posix()

    return DatasetArtifact(
        relative_path=relative,
        sha256=sha256_file(source),
        size_bytes=source.stat().st_size,
        media_type=media_type,
        record_count=record_count,
    )


def load_manifest(path: str | Path) -> DatasetManifest:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig") as handle:
        document = json.load(handle)

    if not isinstance(document, dict):
        raise ValueError("manifest must contain a JSON object.")

    return manifest_from_document(document)


def write_manifest(path: str | Path, manifest: DatasetManifest) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            manifest.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return destination


def manifest_from_document(document: Mapping[str, Any]) -> DatasetManifest:
    artifacts = tuple(
        DatasetArtifact(
            relative_path=str(item["relative_path"]),
            sha256=str(item["sha256"]),
            size_bytes=int(item["size_bytes"]),
            media_type=str(
                item.get("media_type", "application/octet-stream")
            ),
            record_count=(
                int(item["record_count"])
                if item.get("record_count") is not None
                else None
            ),
        )
        for item in document["artifacts"]
    )

    provenance_document = document["provenance"]
    provenance = ProvenanceRecord(
        source_type=str(provenance_document["source_type"]),
        source_reference=str(
            provenance_document["source_reference"]
        ),
        generated_by=str(provenance_document["generated_by"]),
        generated_at_utc=str(
            provenance_document["generated_at_utc"]
        ),
        parameters=dict(provenance_document.get("parameters", {})),
        parent_dataset_ids=tuple(
            str(item)
            for item in provenance_document.get(
                "parent_dataset_ids",
                [],
            )
        ),
        notes=(
            str(provenance_document["notes"])
            if provenance_document.get("notes") is not None
            else None
        ),
    )

    splits = tuple(
        DatasetSplit(
            name=str(item["name"]),
            artifact_paths=tuple(
                str(path)
                for path in item["artifact_paths"]
            ),
            purpose=(
                str(item["purpose"])
                if item.get("purpose") is not None
                else None
            ),
        )
        for item in document.get("splits", [])
    )

    return DatasetManifest(
        dataset_id=str(document["dataset_id"]),
        name=str(document["name"]),
        version=str(document["version"]),
        description=str(document.get("description", "")),
        sequence_type=str(document["sequence_type"]),
        schema_version=str(document.get("schema_version", "1.0")),
        artifacts=artifacts,
        provenance=provenance,
        splits=splits,
        metadata=dict(document.get("metadata", {})),
    )
