from __future__ import annotations

import ast
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<28} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    print("PrimeAIExplorer v1.1.1 Validator")
    print("=" * 76)

    plugin_path = ROOT / "plugins" / "left_twin.py"
    synthetic_test = ROOT / "tests" / "test_exp000002_v11.py"
    compatibility_test = ROOT / "tests" / "test_v111_compatibility.py"

    for path in (plugin_path, synthetic_test, compatibility_test):
        check("Required file", path.exists(), str(path))
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        check("Python syntax", True, str(path))

    module = importlib.import_module("plugins.left_twin")
    current = getattr(module, "is_prime_64", None)
    legacy = getattr(module, "is_probable_prime_64", None)

    check("Current primality API", callable(current), "is_prime_64")
    check("Legacy primality API", callable(legacy), "is_probable_prime_64")
    check("Alias identity", legacy is current, "legacy API aliases current API")

    test_text = synthetic_test.read_text(encoding="utf-8")
    check(
        "Synthetic target count",
        '"target_count": 10' in test_text,
        "target_count=10",
    )
    check(
        "Synthetic endpoint",
        '"endpoints": [9]' in test_text,
        "endpoint=9",
    )
    check(
        "Synthetic target",
        'held_out_target_value"], 107' in test_text,
        "held-out target=107",
    )

    version_path = ROOT / "VERSION"
    check("VERSION file", version_path.exists(), str(version_path))
    version = version_path.read_text(encoding="utf-8").strip()
    check("Version", version == "1.1.1", version)

    print("=" * 76)
    print("PrimeAIExplorer v1.1.1 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
