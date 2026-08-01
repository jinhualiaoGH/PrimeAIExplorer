from __future__ import annotations

import json
from pathlib import Path

from .canonical import sha256_file


def verify_bundle(bundle_root: Path) -> dict[str, object]:
    bundle_root = bundle_root.resolve()
    manifest_path = bundle_root / "manifest.json"

    errors: list[str] = []
    records: list[dict[str, object]] = []

    if not manifest_path.exists():
        return {
            "success": False,
            "bundle_root": str(bundle_root),
            "errors": ["manifest.json is missing"],
            "records": [],
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for item in manifest.get("artifacts", []):
        relative_path = str(item["relative_path"])
        path = bundle_root / relative_path
        exists = path.is_file()
        actual_size = path.stat().st_size if exists else None
        actual_sha256 = sha256_file(path) if exists else None
        expected_size = int(item["size_bytes"])
        expected_sha256 = str(item["sha256"])

        size_match = actual_size == expected_size
        sha256_match = actual_sha256 == expected_sha256
        success = exists and size_match and sha256_match

        if not success:
            errors.append(f"Verification failed: {relative_path}")

        records.append(
            {
                "relative_path": relative_path,
                "exists": exists,
                "expected_size_bytes": expected_size,
                "actual_size_bytes": actual_size,
                "size_match": size_match,
                "expected_sha256": expected_sha256,
                "actual_sha256": actual_sha256,
                "sha256_match": sha256_match,
            }
        )

    for required in ("environment.json", "reproduce.json"):
        if not (bundle_root / required).is_file():
            errors.append(f"Required file is missing: {required}")

    return {
        "success": not errors,
        "bundle_root": str(bundle_root),
        "artifact_count": len(records),
        "errors": errors,
        "records": records,
    }
