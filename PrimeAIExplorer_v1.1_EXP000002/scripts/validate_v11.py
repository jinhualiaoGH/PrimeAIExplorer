from __future__ import annotations

import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<26} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    print("PrimeAIExplorer v1.1 Validator")
    print("=" * 76)

    required = [
        ROOT / "plugins" / "left_twin.py",
        ROOT / "core" / "baselines.py",
        ROOT / "core" / "run_summary.py",
        ROOT / "run_experiment.py",
        ROOT / "experiments" / "EXP-000002" / "config" / "experiment.json",
    ]
    for path in required:
        check("Required file", path.exists(), str(path))

    for path in required:
        if path.suffix == ".py":
            py_compile.compile(str(path), doraise=True)
            check("Python compilation", True, str(path))

    config_path = required[-1]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    check("Experiment ID", config["experiment"]["id"] == "EXP-000002", "EXP-000002")
    check("Experiment version", config["experiment"]["version"] == "1.1.0", "1.1.0")
    check("Sequence plugin", config["sequence"]["plugin"] == "left_twin", "left_twin")
    check("Target count", config["sequence"]["target_count"] == 100000001, "100,000,001")
    print("=" * 76)
    print("PrimeAIExplorer v1.1 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
