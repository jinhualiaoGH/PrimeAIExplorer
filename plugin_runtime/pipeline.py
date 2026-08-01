from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from execution import ExecutionEngine, ExecutionRecord, ExecutionRequest
from kernel.exceptions import ConfigurationError
from plugin_runtime.capabilities import CapabilityResolver
from plugin_runtime.lifecycle import PluginLifecycle, PluginState
from plugin_runtime.loader import PluginLoader
from plugin_runtime.registry import ManifestRegistry


@dataclass
class PluginExecutionPipeline:
    engine: ExecutionEngine
    registry: ManifestRegistry
    loader: PluginLoader = field(default_factory=PluginLoader)
    _lifecycles: dict[str, PluginLifecycle] = field(
        default_factory=dict
    )

    @property
    def resolver(self) -> CapabilityResolver:
        return CapabilityResolver(self.registry)

    def activate(
        self,
        plugin_id: str,
    ) -> PluginLifecycle:
        manifest = self.registry.resolve(plugin_id)
        plugin = self.loader.load(manifest)

        lifecycle = self._lifecycles.get(plugin_id)
        if lifecycle is None or lifecycle.state is PluginState.CLOSED:
            lifecycle = PluginLifecycle(plugin_id=plugin_id)
            self._lifecycles[plugin_id] = lifecycle
            lifecycle.loaded()

        if lifecycle.state is PluginState.LOADED:
            healthy = lifecycle.health_check(
                plugin,
                self.engine.session.context,
            )
        elif lifecycle.state is PluginState.UNHEALTHY:
            healthy = lifecycle.health_check(
                plugin,
                self.engine.session.context,
            )
        else:
            healthy = lifecycle.state is PluginState.READY

        if not healthy:
            raise ConfigurationError(
                f"Plugin health check failed: {plugin_id}"
            )

        if plugin_id not in self.engine.dispatcher.registered_ids():
            self.engine.dispatcher.register(plugin)
        return lifecycle

    def submit(
        self,
        *,
        execution_id: str,
        capability: str,
        payload: Any,
        metadata: Mapping[str, Any] | None = None,
        preferred_plugin_id: str | None = None,
    ) -> ExecutionRequest:
        manifest = self.resolver.resolve(
            capability,
            preferred_plugin_id=preferred_plugin_id,
        )
        self.activate(manifest.plugin_id)
        request = ExecutionRequest.create(
            execution_id=execution_id,
            plugin_id=manifest.plugin_id,
            session_id=self.engine.session.context.session_id,
            payload=payload,
            metadata={
                **dict(metadata or {}),
                "capability": capability,
                "plugin_version": manifest.plugin_version,
                "manifest_sha256": manifest.manifest_sha256,
            },
        )
        self.engine.submit(request)
        return request

    def execute(
        self,
        *,
        execution_id: str,
        capability: str,
        payload: Any,
        metadata: Mapping[str, Any] | None = None,
        preferred_plugin_id: str | None = None,
    ) -> ExecutionRecord:
        self.submit(
            execution_id=execution_id,
            capability=capability,
            payload=payload,
            metadata=metadata,
            preferred_plugin_id=preferred_plugin_id,
        )
        return self.engine.execute_next()

    def close_plugin(self, plugin_id: str) -> None:
        lifecycle = self._lifecycles.get(plugin_id)
        if lifecycle is None:
            raise ConfigurationError(
                f"Plugin has not been activated: {plugin_id}"
            )
        plugin = self.loader.unload(plugin_id)
        lifecycle.close(plugin)
        if plugin_id in self.engine.dispatcher.registered_ids():
            self.engine.dispatcher.unregister(plugin_id)

    def lifecycle(self, plugin_id: str) -> PluginLifecycle:
        if plugin_id not in self._lifecycles:
            raise ConfigurationError(
                f"Plugin has not been activated: {plugin_id}"
            )
        return self._lifecycles[plugin_id]

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "registered_manifests": list(
                self.registry.registered_ids()
            ),
            "loaded_plugins": list(self.loader.loaded_ids()),
            "lifecycles": {
                plugin_id: lifecycle.snapshot()
                for plugin_id, lifecycle in sorted(
                    self._lifecycles.items()
                )
            },
            "engine_snapshot_sha256": self.engine.snapshot_sha256,
        }
