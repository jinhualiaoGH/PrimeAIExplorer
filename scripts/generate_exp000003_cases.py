from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prime_value_cases import PrimeValueCaseEngine


CONFIG = ROOT / "experiments" / "EXP-000003" / "config" / "experiment.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    engine = PrimeValueCaseEngine(config, project_root=ROOT)

    if args.dry_run:
        print(json.dumps(engine.plan().to_dict(), indent=2))
        return 0

    manifest = engine.generate(overwrite=args.overwrite)
    print(json.dumps({
        "experiment_id": manifest["experiment_id"],
        "total_case_count": manifest["total_case_count"],
        "window_sizes": manifest["window_sizes"],
        "case_count_per_window": manifest["case_count_per_window"],
        "dataset_sha256": manifest["dataset_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
    }, indent=2))
    print("[PASS] EXP-000003 cases and prompts generated atomically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
