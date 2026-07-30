from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.release_hardening import ReleaseHardening, atomic_write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()

    hardening = ReleaseHardening(ROOT)
    report = hardening.acceptance(run_tests=not args.skip_tests)

    if (
        not args.allow_dirty
        and report["git"]["available"]
        and not report["git"]["clean"]
    ):
        report["accepted"] = False
        report["dirty_git_rejected"] = True

    release_root = ROOT / "release"
    release_root.mkdir(parents=True, exist_ok=True)
    atomic_write_json(
        release_root / "v1.3.0_acceptance_report.json",
        report,
    )

    if not report["accepted"]:
        print(json.dumps(report, indent=2))
        print("[FAIL] Release package was not built.")
        return 1

    manifest = hardening.release_manifest()
    atomic_write_json(
        release_root / "v1.3.0_release_manifest.json",
        manifest,
    )
    artifact = hardening.build_zip(
        release_root / "PrimeAIExplorer-v1.3.0.zip",
        manifest,
    )
    atomic_write_json(
        release_root / "v1.3.0_release_artifact.json",
        {
            "release_version": "1.3.0",
            "release_manifest_sha256": manifest["manifest_sha256"],
            **artifact,
        },
    )

    print(json.dumps({
        "accepted": True,
        "file_count": manifest["file_count"],
        "manifest_sha256": manifest["manifest_sha256"],
        **artifact,
    }, indent=2))
    print("[PASS] PrimeAIExplorer v1.3.0 release package built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
