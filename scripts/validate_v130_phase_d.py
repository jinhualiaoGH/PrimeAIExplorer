from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prime_value_evaluation import (
    PrimeValueEvaluationEngine,
    ResponseParser,
    LeaderboardBuilder,
)


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<32} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    config_path = ROOT / "experiments" / "EXP-000003" / "config" / "experiment.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    print("PrimeAIExplorer v1.3 Phase D Validator")
    print("=" * 76)
    check("experiment version", config["experiment"]["version"] == "1.3.0-phase-d", config["experiment"]["version"])
    check("evaluation enabled", config["validation"]["phase"] == "response_evaluation", config["validation"]["phase"])
    check("installed version", version == "1.3.0-phase-d", version)
    check("evaluation engine", PrimeValueEvaluationEngine.engine_version == "1.3.0", PrimeValueEvaluationEngine.engine_version)
    check("response parser", ResponseParser.required_fields == ("prediction","confidence","explanation"), str(ResponseParser.required_fields))
    check("leaderboard builder", LeaderboardBuilder.schema_version == "1.0", LeaderboardBuilder.schema_version)
    print("=" * 76)
    print("PrimeAIExplorer v1.3 Phase D validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
