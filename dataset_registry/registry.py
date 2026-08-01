"""Immutable versioned dataset registry."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .io import load_manifest, write_manifest
from .models import DatasetManifest
from .validation import validate_manifest, verify_artifacts


class DatasetRegistry:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def register(
        self,
        dataset_directory: str | Path,
        manifest: DatasetManifest,
    ) -> Path:
        errors = validate_manifest(manifest)
        if errors:
            raise ValueError("; ".join(errors))

        verification = verify_artifacts(dataset_directory, manifest)
        failures = [
            item
            for item in verification
            if not item["exists"]
            or not item["size_match"]
            or not item["sha256_match"]
        ]
        if failures:
            raise ValueError(
                "artifact verification failed for: "
                + ", ".join(item["relative_path"] for item in failures)
            )

        destination = self.root / manifest.dataset_id
        if destination.exists():
            existing = load_manifest(destination / "manifest.json")
            if existing.to_dict() != manifest.to_dict():
                raise RuntimeError(
                    "dataset_id already exists with different content."
                )
            return destination

        temporary = self.root / f".{manifest.dataset_id}.tmp"
        if temporary.exists():
            shutil.rmtree(temporary)
        temporary.mkdir(parents=True)

        source_root = Path(dataset_directory)
        for artifact in manifest.artifacts:
            source = source_root / artifact.relative_path
            target = temporary / artifact.relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        write_manifest(temporary / "manifest.json", manifest)
        temporary.replace(destination)
        return destination

    def get(self, dataset_id: str) -> DatasetManifest:
        return load_manifest(
            self.root / dataset_id / "manifest.json"
        )

    def list(self) -> list[DatasetManifest]:
        manifests: list[DatasetManifest] = []
        for path in sorted(self.root.glob("DS-*/manifest.json")):
            manifests.append(load_manifest(path))
        return manifests

    def verify(self, dataset_id: str) -> list[dict[str, Any]]:
        manifest = self.get(dataset_id)
        return verify_artifacts(
            self.root / dataset_id,
            manifest,
        )
