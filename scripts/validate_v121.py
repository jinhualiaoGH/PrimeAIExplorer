from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sequence_plugins.loader import PluginRegistry


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<32} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    print("PrimeAIExplorer v1.2.1 Validator")
    print("=" * 84)

    required = [
        ROOT / "sequence_plugins" / "builtin" / "__init__.py",
        ROOT / "sequence_plugins" / "builtin" / "left_twin.py",
        ROOT / "scripts" / "list_sequence_plugins.py",
        ROOT / "tests" / "test_sequence_framework_v121.py",
        ROOT / "registries" / "sequence_plugin_registry.csv",
    ]
    for path in required:
        check("Required file", path.exists(), str(path))
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            check("Python syntax", True, str(path))

    from plugins.left_twin import LeftTwinPlugin, is_prime_64
    check("Verified legacy class API", callable(LeftTwinPlugin), "LeftTwinPlugin")
    for method in (
        "validate_source",
        "build_dataset",
        "validate_dataset",
        "load_dataset",
        "make_window",
        "structural_validity",
    ):
        check(
            f"Legacy method {method}",
            callable(getattr(LeftTwinPlugin, method, None)),
            method,
        )
    check("Legacy primality API", is_prime_64(101), "is_prime_64(101)")

    registry = PluginRegistry.from_path(
        ROOT / "registries" / "sequence_plugin_registry.csv"
    )
    active = registry.identifiers(active_only=True)
    for plugin_id in active:
        plugin = registry.create(plugin_id)
        check(
            f"Dynamic load {plugin_id}",
            plugin.plugin_id == plugin_id,
            plugin.__class__.__name__,
        )

    adapter = registry.create("left_twin")
    check(
        "Adapter structural validity",
        adapter.is_structurally_valid(101),
        "101 and 103 are prime",
    )
    check(
        "Adapter rejects non-twin",
        not adapter.is_structurally_valid(103),
        "103 and 105 are not both prime",
    )

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    check("Version", version == "1.2.1", version)

    print("=" * 84)
    print("PrimeAIExplorer v1.2.1 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
