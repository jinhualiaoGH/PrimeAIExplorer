from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prime_value_evaluation import PrimeValueEvaluationEngine, ResponseParser

CONFIG = ROOT / "experiments" / "EXP-000003" / "config" / "experiment.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    engine = PrimeValueEvaluationEngine(config, project_root=ROOT)
    manifest = engine._load_manifest()
    root = engine.responses_root(args.model_id)
    parser_engine = ResponseParser()

    counts = {
        "expected": manifest["total_case_count"],
        "exists": 0,
        "valid_json": 0,
        "schema_valid": 0,
    }
    for item in manifest["cases"]:
        parsed = parser_engine.parse(
            item["case_id"],
            root / f"{item['case_id']}.json",
        )
        counts["exists"] += int(parsed.response_exists)
        counts["valid_json"] += int(parsed.valid_json)
        counts["schema_valid"] += int(parsed.schema_valid)

    print(json.dumps(counts, indent=2))
    if counts["schema_valid"] != counts["expected"]:
        print("[WARN] One or more responses are missing or invalid.")
        return 1
    print("[PASS] All responses satisfy the Phase D schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
