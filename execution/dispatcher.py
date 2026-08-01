from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from execution.protocols import ExecutablePlugin
from kernel.exceptions import ConfigurationError


@dataclass
class PluginDispatcher:
    _plugins: dict[str, ExecutablePlugin] = field(default_factory=dict)

    def register(
        self,
        plugin: ExecutablePlugin,
        *,
        replace: bool = False,
    ) -> None:
        if not isinstance(plugin, ExecutablePlugin):
            raise ConfigurationError(
                "Plugin must implement plugin_id and execute(payload, context)."
            )
        plugin_id = self._normalize_id(plugin.plugin_id)
        if plugin_id in self._plugins and not replace:
            raise ConfigurationError(
                f"Plugin is already registered: {plugin_id}"
            )
        self._plugins[plugin_id] = plugin

    def resolve(self, plugin_id: str) -> ExecutablePlugin:
        normalized = self._normalize_id(plugin_id)
        if normalized not in self._plugins:
            raise ConfigurationError(
                f"Plugin is not registered: {normalized}"
            )
        return self._plugins[normalized]

    def unregister(self, plugin_id: str) -> ExecutablePlugin:
        normalized = self._normalize_id(plugin_id)
        if normalized not in self._plugins:
            raise ConfigurationError(
                f"Plugin is not registered: {normalized}"
            )
        return self._plugins.pop(normalized)

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._plugins))

    @staticmethod
    def _normalize_id(plugin_id: str) -> str:
        if not isinstance(plugin_id, str):
            raise ConfigurationError("plugin_id must be text.")
        normalized = plugin_id.strip()
        if not normalized:
            raise ConfigurationError("plugin_id must not be empty.")
        return normalized
