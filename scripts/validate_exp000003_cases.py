from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prime_value_cases import PrimeValueCaseEngine


CONFIG = ROOT / "experiments" / "EXP-000003" / "config" / "experiment.json"


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    result = PrimeValueCaseEngine(config, project_root=ROOT).validate()
    print(json.dumps(result, indent=2))
    print("[PASS] EXP-000003 case and prompt validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
