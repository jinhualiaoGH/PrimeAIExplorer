from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from kernel.context import ExecutionContext


@runtime_checkable
class ExecutablePlugin(Protocol):
    plugin_id: str

    def execute(
        self,
        payload: Any,
        context: ExecutionContext,
    ) -> Any:
        """Execute one deterministic unit of work."""
