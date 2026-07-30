from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prime_value_cases import PrimeValueCaseEngine


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<32} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    config_path = ROOT / "experiments" / "EXP-000003" / "config" / "experiment.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    print("PrimeAIExplorer v1.3 Phase C Validator")
    print("=" * 76)
    check("experiment version", config["experiment"]["version"] == "1.3.0-phase-c", config["experiment"]["version"])
    check("window sizes", config["cases"]["window_sizes"] == [4,8,16,32,64], str(config["cases"]["window_sizes"]))
    check("cases per window", config["cases"]["case_count_per_window"] == 100, "100")
    check("sampling seed", config["cases"]["sampling_seed"] == 130003, "130003")
    check("blind prompts", config["prompts"]["disclose_sequence_name"] is False, "true")
    check("installed version", version == "1.3.0-phase-c", version)
    check("engine available", PrimeValueCaseEngine.engine_version == "1.3.0", PrimeValueCaseEngine.engine_version)
    print("=" * 76)
    print("PrimeAIExplorer v1.3 Phase C validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
