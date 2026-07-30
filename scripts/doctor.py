from __future__ import annotations

import importlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.registry import available_plugins


def check(label: str, ok: bool, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label:<24} {detail}")
    if not ok:
        raise SystemExit(1)


def main() -> int:
    print("PrimeAIExplorer v0.2 Doctor")
    print("=" * 72)
    check("Python", sys.version_info >= (3, 11), platform.python_version())
    check("Project root", ROOT.exists(), str(ROOT))

    for module in ("numpy",):
        try:
            imported = importlib.import_module(module)
            check(f"Dependency {module}", True, getattr(imported, "__version__", "installed"))
        except Exception as exc:
            check(f"Dependency {module}", False, str(exc))

    configs = [
        ROOT / "experiments" / "EXP-000001" / "config" / "experiment.json",
        ROOT / "experiments" / "EXP-000002" / "config" / "experiment.json",
    ]
    for path in configs:
        with path.open("r", encoding="utf-8") as f:
            json.load(f)
        check("Configuration", True, str(path.relative_to(ROOT)))

    check("Plugins", True, ", ".join(available_plugins()))
    print("=" * 72)
    print("Doctor completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
