"""Manifest and artifact verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import dataset_id_from_document
from .io import sha256_file
from .models import DatasetManifest


def validate_manifest(manifest: DatasetManifest) -> list[str]:
    errors: list[str] = []

    expected_id = dataset_id_from_document(manifest.to_dict())
    if manifest.dataset_id != expected_id:
        errors.append(
            f"dataset_id mismatch: {manifest.dataset_id} != {expected_id}"
        )

    split_names = [item.name for item in manifest.splits]
    if len(split_names) != len(set(split_names)):
        errors.append("split names must be unique.")

    return errors


def verify_artifacts(
    dataset_directory: str | Path,
    manifest: DatasetManifest,
) -> list[dict[str, Any]]:
    root = Path(dataset_directory)
    results: list[dict[str, Any]] = []

    for artifact in manifest.artifacts:
        path = root / artifact.relative_path
        exists = path.exists()
        actual_size = path.stat().st_size if exists else None
        actual_sha256 = sha256_file(path) if exists else None

        results.append(
            {
                "relative_path": artifact.relative_path,
                "exists": exists,
                "size_match": (
                    actual_size == artifact.size_bytes
                    if exists
                    else False
                ),
                "sha256_match": (
                    actual_sha256 == artifact.sha256
                    if exists
                    else False
                ),
                "expected_size_bytes": artifact.size_bytes,
                "actual_size_bytes": actual_size,
                "expected_sha256": artifact.sha256,
                "actual_sha256": actual_sha256,
            }
        )

    return results
