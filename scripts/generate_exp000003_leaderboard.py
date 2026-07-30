from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prime_value_evaluation import LeaderboardBuilder


def main() -> int:
    experiment_root = ROOT / "experiments" / "EXP-000003"
    leaderboard = LeaderboardBuilder(
        experiment_root / "evaluations"
    ).write(
        experiment_root / "leaderboard"
    )
    print(json.dumps(leaderboard, indent=2))
    print("[PASS] EXP-000003 leaderboard generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
