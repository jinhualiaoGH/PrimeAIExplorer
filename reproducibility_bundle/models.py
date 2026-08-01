from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactRecord:
    relative_path: str
    size_bytes: int
    sha256: str
    source_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "source_path": self.source_path,
        }


@dataclass(frozen=True)
class BundleResult:
    bundle_root: Path
    manifest_path: Path
    artifact_count: int
    archive_path: Path | None

    def to_dict(self) -> dict[str, object]:
        return {
            "bundle_root": str(self.bundle_root),
            "manifest_path": str(self.manifest_path),
            "artifact_count": self.artifact_count,
            "archive_path": None if self.archive_path is None else str(self.archive_path),
        }
