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
    engine = PrimeValueEvaluationEngine(config, project_root=ROOT)
    workspace = engine.prepare_response_workspace(
        args.model_id,
        overwrite=args.overwrite,
    )
    print(json.dumps(workspace, indent=2))
    print("[PASS] Response workspace prepared.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
