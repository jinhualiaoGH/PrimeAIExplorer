from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .archive import build_deterministic_zip
from .canonical import normalize_relative, sha256_file
from .environment import capture_environment
from .io import write_json_atomic
from .models import ArtifactRecord, BundleResult


DEFAULT_EXCLUDES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
}


def _iter_files(source: Path, excludes: set[str]) -> Iterable[Path]:
    if source.is_file():
        yield source
        return

    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        if any(part in excludes for part in path.parts):
            continue
        yield path


def build_bundle(
    *,
    project_root: Path,
    output_root: Path,
    bundle_name: str,
    sources: list[Path],
    command: list[str] | None = None,
    metadata: dict[str, object] | None = None,
    create_archive: bool = True,
    overwrite: bool = False,
    excludes: set[str] | None = None,
) -> BundleResult:
    project_root = project_root.resolve()
    output_root = output_root.resolve()
    bundle_root = output_root / bundle_name

    if bundle_root.exists():
        if not overwrite:
            raise FileExistsError(f"Bundle already exists: {bundle_root}")
        shutil.rmtree(bundle_root)

    artifacts_root = bundle_root / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    effective_excludes = set(DEFAULT_EXCLUDES)
    if excludes:
        effective_excludes.update(excludes)

    records: list[ArtifactRecord] = []
    seen_destinations: set[str] = set()

    for source_arg in sources:
        source = source_arg if source_arg.is_absolute() else project_root / source_arg
        source = source.resolve()
        if not source.exists():
            raise FileNotFoundError(f"Source does not exist: {source}")

        source_base = source.parent if source.is_file() else source
        source_label = source.name

        for file_path in _iter_files(source, effective_excludes):
            inner = file_path.relative_to(source_base)
            relative = Path(source_label) / inner if source.is_dir() else Path(source_label)
            relative_text = normalize_relative(relative)

            if relative_text in seen_destinations:
                raise ValueError(f"Duplicate bundle destination: {relative_text}")
            seen_destinations.add(relative_text)

            destination = artifacts_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, destination)

            records.append(
                ArtifactRecord(
                    relative_path=normalize_relative(destination.relative_to(bundle_root)),
                    size_bytes=destination.stat().st_size,
                    sha256=sha256_file(destination),
                    source_path=str(file_path),
                )
            )

    environment = capture_environment(project_root)
    write_json_atomic(bundle_root / "environment.json", environment)

    reproduce = {
        "schema_version": "1.0",
        "working_directory": str(project_root),
        "command": command or [],
    }
    write_json_atomic(bundle_root / "reproduce.json", reproduce)

    manifest = {
        "schema_version": "1.0",
        "bundle_name": bundle_name,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "project_root": str(project_root),
        "artifact_count": len(records),
        "artifacts": [record.to_dict() for record in sorted(records, key=lambda item: item.relative_path)],
        "metadata": metadata or {},
        "environment_file": "environment.json",
        "reproduce_file": "reproduce.json",
    }
    manifest_path = bundle_root / "manifest.json"
    write_json_atomic(manifest_path, manifest)

    archive_path = None
    if create_archive:
        archive_path = output_root / f"{bundle_name}.zip"
        build_deterministic_zip(bundle_root, archive_path)

    return BundleResult(
        bundle_root=bundle_root,
        manifest_path=manifest_path,
        artifact_count=len(records),
        archive_path=archive_path,
    )
