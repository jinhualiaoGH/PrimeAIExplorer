from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.release_hardening import file_sha256


def main() -> int:
    archive = ROOT / "release" / "PrimeAIExplorer-v1.3.0.zip"
    if not archive.exists():
        raise SystemExit(f"Archive not found: {archive}")

    with zipfile.ZipFile(archive, "r") as zf:
        bad = zf.testzip()
        names = zf.namelist()
        manifest_names = [
            name for name in names
            if name.endswith("/release/release_manifest.json")
        ]
        if bad is not None:
            raise SystemExit(f"Corrupt member: {bad}")
        if len(manifest_names) != 1:
            raise SystemExit("Release manifest missing or duplicated.")
        manifest = json.loads(
            zf.read(manifest_names[0]).decode("utf-8")
        )

    result = {
        "archive": str(archive),
        "archive_sha256": file_sha256(archive),
        "member_count": len(names),
        "manifest_file_count": manifest["file_count"],
        "manifest_sha256": manifest["manifest_sha256"],
        "valid": len(names) == manifest["file_count"] + 1,
    }
    print(json.dumps(result, indent=2))
    if not result["valid"]:
        return 1
    print("[PASS] PrimeAIExplorer v1.3.0 release archive validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
