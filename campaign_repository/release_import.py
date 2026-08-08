from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import zipfile
from typing import Any

from kernel.exceptions import ValidationError

from .release_verify import (
    ScientificReleaseVerifier,
    _safe_zip_name,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class ReleaseImportResult:
    release_id: str
    destination_path: str
    imported_entries: int
    skipped_entries: int
    bundle_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "i6.0",
            "release_id": self.release_id,
            "destination_path": self.destination_path,
            "imported_entries": self.imported_entries,
            "skipped_entries": self.skipped_entries,
            "bundle_sha256": self.bundle_sha256,
        }


class ScientificReleaseImporter:
    def __init__(
        self,
        root: str | Path,
        *,
        verifier: ScientificReleaseVerifier | None = None,
    ):
        self.root = Path(root)
        self.verifier = verifier or ScientificReleaseVerifier()

    def import_bundle(
        self,
        bundle_path: str | Path,
        *,
        expected_bundle_sha256: str | None = None,
    ) -> ReleaseImportResult:
        verification = self.verifier.verify(
            bundle_path,
            expected_bundle_sha256=expected_bundle_sha256,
        )

        if not verification.valid:
            raise ValidationError(
                "release verification failed: "
                + "; ".join(verification.errors)
            )

        if not verification.release_id:
            raise ValidationError(
                "verified release does not contain release_id."
            )

        release_id = verification.release_id
        destination = self.root / "releases" / release_id

        bundle_path = Path(bundle_path)

        with zipfile.ZipFile(bundle_path, "r") as archive:
            names = sorted(archive.namelist())

            for name in names:
                if not _safe_zip_name(name):
                    raise ValidationError(
                        f"unsafe ZIP entry path: {name}"
                    )

            imported = 0
            skipped = 0

            for name in names:
                if name.endswith("/"):
                    continue

                target = self._safe_target(
                    destination,
                    name,
                )
                data = archive.read(name)

                if target.exists():
                    existing = target.read_bytes()
                    if existing == data:
                        skipped += 1
                        continue
                    raise ValidationError(
                        f"import conflict at immutable path: {target}"
                    )

                self._write_immutable(
                    target,
                    data,
                )
                imported += 1

        marker = destination / "release" / "import.json"
        marker_payload = json.dumps(
            {
                "schema_version": "i6.0",
                "release_id": release_id,
                "bundle_sha256": verification.bundle_sha256,
                "release_manifest_sha256": verification.release_manifest_sha256,
                "imported_entries": imported,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        if marker.exists():
            existing = json.loads(
                marker.read_text(encoding="utf-8")
            )
            if existing.get("bundle_sha256") != verification.bundle_sha256:
                raise ValidationError(
                    "release import marker conflicts with bundle SHA-256."
                )
        else:
            self._write_immutable(
                marker,
                marker_payload,
            )

        return ReleaseImportResult(
            release_id=release_id,
            destination_path=str(destination),
            imported_entries=imported,
            skipped_entries=skipped,
            bundle_sha256=verification.bundle_sha256,
        )

    @staticmethod
    def _safe_target(
        destination: Path,
        archive_name: str,
    ) -> Path:
        normalized = archive_name.replace("\\", "/")
        pure = PurePosixPath(normalized)

        if pure.is_absolute() or ".." in pure.parts:
            raise ValidationError(
                f"unsafe import path: {archive_name}"
            )

        target = destination.joinpath(*pure.parts)

        destination_resolved = destination.resolve()
        target_resolved = target.resolve()

        try:
            target_resolved.relative_to(
                destination_resolved
            )
        except ValueError as exc:
            raise ValidationError(
                f"import path escapes destination: {archive_name}"
            ) from exc

        return target

    @staticmethod
    def _write_immutable(
        path: Path,
        data: bytes,
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists():
            if path.read_bytes() == data:
                return
            raise ValidationError(
                f"immutable import path already exists with different content: {path}"
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
