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
    parser.add_argument("--require-clean-git", action="store_true")
    args = parser.parse_args()

    hardening = ReleaseHardening(ROOT)
    report = hardening.acceptance(run_tests=not args.skip_tests)

    if args.require_clean_git:
        report["accepted"] = bool(
            report["accepted"]
            and report["git"]["available"]
            and report["git"]["clean"]
        )

    output = ROOT / "release" / "v1.3.0_acceptance_report.json"
    atomic_write_json(output, report)
    print(json.dumps(report, indent=2))
    print(f"Acceptance report: {output}")

    if not report["accepted"]:
        print("[FAIL] PrimeAIExplorer v1.3.0 release acceptance failed.")
        return 1

    print("[PASS] PrimeAIExplorer v1.3.0 release acceptance passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
