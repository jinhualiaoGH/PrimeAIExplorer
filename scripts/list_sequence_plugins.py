from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sequence_plugins.loader import PluginRegistry


REGISTRY = ROOT / "registries" / "sequence_plugin_registry.csv"


def main() -> int:
    registry = PluginRegistry.from_path(REGISTRY)
    print("PrimeAIExplorer Sequence Plugins")
    print("=" * 96)
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
