"""Build deterministic manifests from dataset directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonical import dataset_id_from_document
from .io import artifact_from_file
from .models import (
    DatasetArtifact,
    DatasetManifest,
    DatasetSplit,
    ProvenanceRecord,
)


def build_manifest(
    dataset_directory: str | Path,
    *,
    name: str,
    version: str,
    description: str,
    sequence_type: str,
    provenance: ProvenanceRecord,
    artifact_paths: Sequence[str],
    splits: Sequence[DatasetSplit] = (),
    metadata: Mapping[str, Any] | None = None,
    media_types: Mapping[str, str] | None = None,
    record_counts: Mapping[str, int] | None = None,
    schema_version: str = "1.0",
) -> DatasetManifest:
    root = Path(dataset_directory)
    media_types = dict(media_types or {})
    record_counts = dict(record_counts or {})

    artifacts = tuple(
        artifact_from_file(
            root,
            root / relative_path,
            media_type=media_types.get(
                relative_path,
                "application/octet-stream",
            ),
            record_count=record_counts.get(relative_path),
        )
        for relative_path in artifact_paths
    )

    provisional = {
        "name": name,
        "version": version,
        "description": description,
        "sequence_type": sequence_type,
        "schema_version": schema_version,
        "artifacts": [item.to_dict() for item in artifacts],
        "provenance": provenance.to_dict(),
        "splits": [item.to_dict() for item in splits],
        "metadata": dict(metadata or {}),
    }
    dataset_id = dataset_id_from_document(provisional)

    return DatasetManifest(
        dataset_id=dataset_id,
        name=name,
        version=version,
        description=description,
        sequence_type=sequence_type,
        schema_version=schema_version,
        artifacts=artifacts,
        provenance=provenance,
        splits=tuple(splits),
        metadata=dict(metadata or {}),
    )
