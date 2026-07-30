from __future__ import annotations

import ast
from pathlib import Path

from sequence_plugins.loader import PluginRegistry


ROOT = Path(__file__).resolve().parents[1]


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<30} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    print("PrimeAIExplorer v1.2.0 Validator")
    print("=" * 82)

    required = [
        ROOT / "sequence_plugins" / "base.py",
        ROOT / "sequence_plugins" / "loader.py",
        ROOT / "sequence_plugins" / "registry.py",
        ROOT / "sequence_plugins" / "builtin" / "left_twin.py",
        ROOT / "registries" / "sequence_plugin_registry.csv",
        ROOT / "registries" / "sequence_plugin_registry.json",
        ROOT / "tests" / "test_sequence_framework_v120.py",
    ]

    for path in required:
        check("Required file", path.exists(), str(path))
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            check("Python syntax", True, str(path))

    csv_registry = PluginRegistry.from_path(
        ROOT / "registries" / "sequence_plugin_registry.csv"
    )
    json_registry = PluginRegistry.from_path(
        ROOT / "registries" / "sequence_plugin_registry.json"
    )

    check(
        "Registry agreement",
        csv_registry.identifiers() == json_registry.identifiers(),
        f"{len(csv_registry.identifiers())} plugin records",
    )

    active = csv_registry.identifiers(active_only=True)
    check("Active plugin count", len(active) >= 5, str(active))

    for plugin_id in active:
        plugin = csv_registry.create(plugin_id)
        check(
            f"Load plugin {plugin_id}",
            plugin.plugin_id == plugin_id,
            plugin.__class__.__name__,
        )

    version_path = ROOT / "VERSION"
    check("VERSION file", version_path.exists(), str(version_path))
    version = version_path.read_text(encoding="utf-8").strip()
    check("Version", version == "1.2.0", version)

    print("=" * 82)
    print("PrimeAIExplorer v1.2.0 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
