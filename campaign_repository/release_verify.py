from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile
from typing import Any

from kernel.exceptions import ValidationError
from experimental_campaign.identity import sha256_json


_REQUIRED_RELEASE_FILES = {
    "release/manifest.json",
    "release/index.json",
    "release/checksums.sha256",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_zip_name(name: str) -> bool:
    if not isinstance(name, str) or not name:
        return False
    normalized = name.replace("\\", "/")
    if normalized.startswith("/"):
        return False
    path = PurePosixPath(normalized)
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    return True


def _parse_checksum_manifest(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "  " not in line:
            raise ValidationError(
                "invalid checksum manifest line."
            )
        digest, path = line.split("  ", 1)
        digest = digest.strip().lower()
        path = path.strip().replace("\\", "/")

        if len(digest) != 64 or any(
            char not in "0123456789abcdef"
            for char in digest
        ):
            raise ValidationError(
                "invalid SHA-256 in checksum manifest."
            )
        if not _safe_zip_name(path):
            raise ValidationError(
                "unsafe path in checksum manifest."
            )
        if path in result:
            raise ValidationError(
                f"duplicate checksum path: {path}"
            )
        result[path] = digest
    return result


@dataclass(frozen=True, slots=True)
class ReleaseVerificationResult:
    bundle_path: str
    bundle_sha256: str
    valid: bool
    release_id: str | None
    release_manifest_sha256: str | None
    checked_entries: int
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "i6.0",
            "bundle_path": self.bundle_path,
            "bundle_sha256": self.bundle_sha256,
            "valid": self.valid,
            "release_id": self.release_id,
            "release_manifest_sha256": self.release_manifest_sha256,
            "checked_entries": self.checked_entries,
            "errors": list(self.errors),
        }


class ScientificReleaseVerifier:
    def verify(
        self,
        bundle_path: str | Path,
        *,
        expected_bundle_sha256: str | None = None,
    ) -> ReleaseVerificationResult:
        bundle_path = Path(bundle_path)
        if not bundle_path.is_file():
            raise FileNotFoundError(bundle_path)

        bundle_bytes = bundle_path.read_bytes()
        bundle_sha256 = _sha256_bytes(bundle_bytes)

        errors: list[str] = []
        release_id: str | None = None
        release_manifest_sha256: str | None = None
        checked_entries = 0

        if expected_bundle_sha256 is not None:
            expected = expected_bundle_sha256.strip().lower()
            if bundle_sha256 != expected:
                errors.append("bundle_sha256_mismatch")

        try:
            with zipfile.ZipFile(bundle_path, "r") as archive:
                names = archive.namelist()

                if len(names) != len(set(names)):
                    errors.append("duplicate_zip_entries")

                for name in names:
                    if not _safe_zip_name(name):
                        errors.append(f"unsafe_zip_path:{name}")

                missing = sorted(
                    _REQUIRED_RELEASE_FILES - set(names)
                )
                for name in missing:
                    errors.append(f"missing_required_file:{name}")

                if errors and missing:
                    return ReleaseVerificationResult(
                        bundle_path=str(bundle_path),
                        bundle_sha256=bundle_sha256,
                        valid=False,
                        release_id=None,
                        release_manifest_sha256=None,
                        checked_entries=0,
                        errors=tuple(errors),
                    )

                manifest_bytes = archive.read(
                    "release/manifest.json"
                )
                index_bytes = archive.read(
                    "release/index.json"
                )
                checksums_bytes = archive.read(
                    "release/checksums.sha256"
                )

                manifest = json.loads(
                    manifest_bytes.decode("utf-8")
                )
                index = json.loads(
                    index_bytes.decode("utf-8")
                )
                checksums = _parse_checksum_manifest(
                    checksums_bytes.decode("utf-8")
                )

                release_id = manifest.get("release_id")
                release_manifest_sha256 = manifest.get(
                    "release_manifest_sha256"
                )

                manifest_identity_payload = {
                    "schema_version": manifest.get("schema_version"),
                    "release_name": manifest.get("release_name"),
                    "campaign_id": manifest.get("campaign_id"),
                    "experiment_id": manifest.get("experiment_id"),
                    "components": manifest.get("components", []),
                    "metadata": manifest.get("metadata", {}),
                }
                actual_manifest_identity = sha256_json(
                    manifest_identity_payload
                )
                if (
                    release_manifest_sha256
                    != actual_manifest_identity
                ):
                    errors.append(
                        "release_manifest_sha256_mismatch"
                    )

                if (
                    index.get("release_id")
                    != release_id
                ):
                    errors.append(
                        "index_release_id_mismatch"
                    )

                if (
                    index.get("release_manifest_sha256")
                    != release_manifest_sha256
                ):
                    errors.append(
                        "index_manifest_sha256_mismatch"
                    )

                if (
                    index.get("campaign_id")
                    != manifest.get("campaign_id")
                ):
                    errors.append(
                        "index_campaign_id_mismatch"
                    )

                if (
                    index.get("experiment_id")
                    != manifest.get("experiment_id")
                ):
                    errors.append(
                        "index_experiment_id_mismatch"
                    )

                components = manifest.get("components", [])
                if not isinstance(components, list):
                    errors.append(
                        "manifest_components_not_list"
                    )
                    components = []

                component_paths: set[str] = set()
                component_ids: set[str] = set()

                for component in components:
                    if not isinstance(component, dict):
                        errors.append(
                            "invalid_component_record"
                        )
                        continue

                    cid = component.get("component_id")
                    path = str(
                        component.get("relative_path", "")
                    ).replace("\\", "/")
                    expected_sha = component.get("sha256")

                    if cid in component_ids:
                        errors.append(
                            f"duplicate_component_id:{cid}"
                        )
                    component_ids.add(cid)

                    if path in component_paths:
                        errors.append(
                            f"duplicate_component_path:{path}"
                        )
                    component_paths.add(path)

                    if not _safe_zip_name(path):
                        errors.append(
                            f"unsafe_component_path:{path}"
                        )
                        continue

                    if path not in names:
                        errors.append(
                            f"missing_component:{path}"
                        )
                        continue

                    payload = archive.read(path)
                    checked_entries += 1
                    actual_sha = _sha256_bytes(payload)

                    if actual_sha != expected_sha:
                        errors.append(
                            f"component_sha256_mismatch:{path}"
                        )

                    checksum_sha = checksums.get(path)
                    if checksum_sha is None:
                        errors.append(
                            f"checksum_missing:{path}"
                        )
                    elif checksum_sha != actual_sha:
                        errors.append(
                            f"checksum_mismatch:{path}"
                        )

                actual_manifest_file_sha = _sha256_bytes(
                    manifest_bytes
                )
                checksum_manifest_sha = checksums.get(
                    "release/manifest.json"
                )
                if checksum_manifest_sha is None:
                    errors.append(
                        "checksum_missing:release/manifest.json"
                    )
                elif (
                    checksum_manifest_sha
                    != actual_manifest_file_sha
                ):
                    errors.append(
                        "checksum_mismatch:release/manifest.json"
                    )

                index_components = index.get(
                    "components",
                    []
                )
                if isinstance(index_components, list):
                    index_map = {
                        str(item.get("component_id")): item
                        for item in index_components
                        if isinstance(item, dict)
                    }
                    for component in components:
                        if not isinstance(component, dict):
                            continue
                        cid = str(component.get("component_id"))
                        indexed = index_map.get(cid)
                        if indexed is None:
                            errors.append(
                                f"index_missing_component:{cid}"
                            )
                            continue
                        for field in (
                            "kind",
                            "relative_path",
                            "sha256",
                        ):
                            if indexed.get(field) != component.get(field):
                                errors.append(
                                    f"index_component_mismatch:{cid}:{field}"
                                )
                else:
                    errors.append("index_components_not_list")

        except zipfile.BadZipFile:
            errors.append("invalid_zip")
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(
                f"invalid_release_json:{exc.__class__.__name__}"
            )
        except ValidationError as exc:
            errors.append(f"invalid_checksums:{exc}")

        return ReleaseVerificationResult(
            bundle_path=str(bundle_path),
            bundle_sha256=bundle_sha256,
            valid=(len(errors) == 0),
            release_id=release_id,
            release_manifest_sha256=release_manifest_sha256,
            checked_entries=checked_entries,
            errors=tuple(errors),
        )
