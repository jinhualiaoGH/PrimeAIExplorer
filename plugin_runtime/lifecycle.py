from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from execution.protocols import ExecutablePlugin
from kernel.context import ExecutionContext
from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256


class PluginState(str, Enum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    READY = "ready"
    UNHEALTHY = "unhealthy"
    CLOSED = "closed"


_ALLOWED = {
    PluginState.DISCOVERED: {PluginState.LOADED},
    PluginState.LOADED: {
        PluginState.READY,
        PluginState.UNHEALTHY,
        PluginState.CLOSED,
    },
    PluginState.READY: {
        PluginState.UNHEALTHY,
        PluginState.CLOSED,
    },
    PluginState.UNHEALTHY: {
        PluginState.READY,
        PluginState.CLOSED,
    },
    PluginState.CLOSED: set(),
}


@dataclass
class PluginLifecycle:
    plugin_id: str
    state: PluginState = PluginState.DISCOVERED
    health_detail: dict[str, Any] = field(default_factory=dict)

    def loaded(self) -> None:
        self._transition(PluginState.LOADED)

    def health_check(
        self,
        plugin: ExecutablePlugin,
        context: ExecutionContext,
    ) -> bool:
        checker = getattr(plugin, "health_check", None)
        try:
            healthy = True if checker is None else bool(
                checker(context)
            )
        except Exception as exc:
            self.health_detail = {
                "healthy": False,
                "error_type": type(exc).__name__,
                "error_message": str(exc) or type(exc).__name__,
            }
            self._transition(PluginState.UNHEALTHY)
            return False

        self.health_detail = {"healthy": healthy}
        self._transition(
            PluginState.READY
            if healthy
            else PluginState.UNHEALTHY
        )
        return healthy

    def close(self, plugin: ExecutablePlugin) -> None:
        closer = getattr(plugin, "close", None)
        if closer is not None:
            closer()
        self._transition(PluginState.CLOSED)

    def snapshot(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "state": self.state.value,
            "health_detail": self.health_detail,
        }

    @property
    def snapshot_sha256(self) -> str:
        return stable_sha256(self.snapshot())

    def _transition(self, target: PluginState) -> None:
        if target not in _ALLOWED[self.state]:
            raise ValidationError(
                "Invalid plugin lifecycle transition: "
                f"{self.state.value} -> {target.value}"
            )
        self.state = target
