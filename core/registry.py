from __future__ import annotations

from typing import Any

from core.plugin import SequencePlugin
from plugins.left_twin import LeftTwinPlugin
from plugins.prime_gap import PrimeGapPlugin


_PLUGIN_TYPES: dict[str, type[SequencePlugin]] = {
    "prime_gap": PrimeGapPlugin,
    "left_twin": LeftTwinPlugin,
}


def create_plugin(config: dict[str, Any]) -> SequencePlugin:
    name = config["sequence"]["plugin"]
    try:
        plugin_type = _PLUGIN_TYPES[name]
    except KeyError as exc:
        available = ", ".join(sorted(_PLUGIN_TYPES))
        raise ValueError(f"Unknown sequence plugin '{name}'. Available: {available}") from exc
    return plugin_type(config)


def available_plugins() -> list[str]:
    return sorted(_PLUGIN_TYPES)
