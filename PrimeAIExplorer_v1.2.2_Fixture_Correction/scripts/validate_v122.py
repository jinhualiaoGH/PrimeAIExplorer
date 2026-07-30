from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sequence_plugins.loader import PluginRegistry


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<34} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    print("PrimeAIExplorer v1.2.2 Validator")
    print("=" * 86)

    registry_path = ROOT / "registries" / "sequence_plugin_registry.csv"
    registry = PluginRegistry.from_path(registry_path)
    record = registry.get("left_twin")
    plugin = registry.create("left_twin")

    check("Registry Left Twin version", record.version == "1.2.2", record.version)
    check(
        "Adapter Left Twin version",
        plugin.plugin_version == "1.2.2",
        plugin.plugin_version,
    )
    check(
        "Registry/adapter agreement",
        record.version == plugin.plugin_version,
        f"{record.version} == {plugin.plugin_version}",
    )
    check(
        "Adapter structural validity",
        plugin.is_structurally_valid(101),
        "101 and 103 are prime",
    )

    test_path = ROOT / "tests" / "test_sequence_framework_v121.py"
    text = test_path.read_text(encoding="utf-8")
    check("Fixture expected count", 'target_count": 6' in text, "6")
    check(
        "Fixture exact values",
        "[3, 5, 11, 17, 29, 41]" in text,
        "six left twin values",
    )

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    check("Version", version == "1.2.2", version)

    print("=" * 86)
    print("PrimeAIExplorer v1.2.2 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
