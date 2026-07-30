from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prime_value_evaluation import PrimeValueEvaluationEngine

CONFIG = ROOT / "experiments" / "EXP-000003" / "config" / "experiment.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    summary = PrimeValueEvaluationEngine(
        config,
        project_root=ROOT,
    ).evaluate(
        args.model_id,
        overwrite=args.overwrite,
    )
    print(json.dumps({
        "experiment_id": summary["experiment_id"],
        "model_id": summary["model_id"],
        "case_count": summary["overall"]["case_count"],
        "correct_count": summary["overall"]["correct_count"],
        "exact_accuracy": summary["overall"]["exact_accuracy"],
        "valid_json_rate": summary["overall"]["valid_json_rate"],
        "schema_valid_rate": summary["overall"]["schema_valid_rate"],
        "prime_valid_rate": summary["overall"]["prime_valid_rate"],
        "summary_sha256": summary["summary_sha256"],
    }, indent=2))
    print("[PASS] EXP-000003 responses evaluated atomically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
