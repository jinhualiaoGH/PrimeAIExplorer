from __future__ import annotations

from pathlib import Path

from sequence_plugins.loader import PluginRegistry


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registries" / "sequence_plugin_registry.csv"


def main() -> int:
    registry = PluginRegistry.from_path(REGISTRY)
    print("PrimeAIExplorer Sequence Plugins")
    print("=" * 88)
    for plugin_id in registry.identifiers():
        record = registry.get(plugin_id)
        print(
            f"{record.plugin_id:<20} "
            f"{record.version:<10} "
            f"{record.status:<9} "
            f"{record.source_type:<20} "
            f"{record.description}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
