from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

from execution.protocols import ExecutablePlugin
from kernel.exceptions import ConfigurationError
from plugin_runtime.manifest import PluginManifest


@dataclass
class PluginLoader:
    _instances: dict[str, ExecutablePlugin] = field(
        default_factory=dict
    )

    def load(
        self,
        manifest: PluginManifest,
        *,
        reload: bool = False,
    ) -> ExecutablePlugin:
        if not manifest.enabled:
            raise ConfigurationError(
                f"Plugin is disabled: {manifest.plugin_id}"
            )
        if manifest.plugin_id in self._instances and not reload:
            return self._instances[manifest.plugin_id]

        try:
            module = import_module(manifest.module)
        except Exception as exc:
            raise ConfigurationError(
                f"Could not import plugin module: {manifest.module}"
            ) from exc

        try:
            plugin_class = getattr(module, manifest.class_name)
        except AttributeError as exc:
            raise ConfigurationError(
                "Plugin class does not exist: "
                f"{manifest.module}.{manifest.class_name}"
            ) from exc

        instance = self._construct(
            plugin_class,
            dict(manifest.configuration),
        )
        if not isinstance(instance, ExecutablePlugin):
            raise ConfigurationError(
                "Loaded object does not implement ExecutablePlugin: "
                f"{manifest.plugin_id}"
            )
        actual_id = instance.plugin_id.strip()
        if actual_id != manifest.plugin_id:
            raise ConfigurationError(
                "Loaded plugin_id does not match manifest: "
                f"{actual_id!r} != {manifest.plugin_id!r}"
            )
        self._instances[manifest.plugin_id] = instance
        return instance

    def unload(self, plugin_id: str) -> ExecutablePlugin:
        if plugin_id not in self._instances:
            raise ConfigurationError(
                f"Plugin is not loaded: {plugin_id}"
            )
        return self._instances.pop(plugin_id)

    def loaded_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._instances))

    @staticmethod
    def _construct(
        plugin_class: type[Any],
        configuration: dict[str, Any],
    ) -> Any:
        try:
            return plugin_class(configuration=configuration)
        except TypeError:
            try:
                return plugin_class(**configuration)
            except TypeError:
                if configuration:
                    raise ConfigurationError(
                        "Plugin constructor rejected manifest "
                        "configuration."
                    )
                return plugin_class()
