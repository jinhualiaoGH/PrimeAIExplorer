from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from kernel.context import ExecutionContext
from kernel.events import (
    KernelEvent,
    KernelEventType,
    validate_event_sequence,
)
from kernel.exceptions import ValidationError
from kernel.result import ExecutionResult
from kernel.serialization import stable_sha256
from runtime.configuration import RuntimeConfiguration
from runtime.dispatcher import EventBus
from runtime.lifecycle import RuntimeState, validate_transition
from runtime.registry import ServiceRegistry


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


@dataclass
class RuntimeSession:
    context: ExecutionContext
    configuration: RuntimeConfiguration
    services: ServiceRegistry = field(default_factory=ServiceRegistry)
    events: EventBus = field(default_factory=EventBus)
    state: RuntimeState = RuntimeState.CREATED
    result: ExecutionResult | None = None
    _sequence: int = 0

    def __post_init__(self) -> None:
        self._emit(
            KernelEventType.RUN_CREATED,
            {"state": self.state.value},
        )

    def initialize(self) -> None:
        self._transition(RuntimeState.INITIALIZED)
        self._emit(
            KernelEventType.RUN_STARTED,
            {"phase": "initialized"},
        )

    def start(self) -> None:
        self._transition(RuntimeState.RUNNING)
        self._emit(
            KernelEventType.BENCHMARK_LOADED,
            {"benchmark_id": self.context.benchmark_id},
        )

    def finish(self, result: ExecutionResult) -> None:
        if result.session_id != self.context.session_id:
            raise ValidationError(
                "ExecutionResult session_id does not match RuntimeSession."
            )
        self._transition(RuntimeState.FINISHED)
        self.result = result
        self._emit(
            KernelEventType.RESULT_CREATED,
            {"status": result.status.value},
        )
        self._emit(
            KernelEventType.RUN_FINISHED,
            {"status": result.status.value},
        )
        validate_event_sequence(list(self.events.history()))

    def fail(self, message: str) -> None:
        if not isinstance(message, str) or not message.strip():
            raise ValidationError("Failure message must not be empty.")
        self._transition(RuntimeState.FAILED)
        self._emit(
            KernelEventType.RUN_FAILED,
            {"message": message.strip()},
        )

    def close(self) -> None:
        self._transition(RuntimeState.CLOSED)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "session_id": self.context.session_id,
            "state": self.state.value,
            "context_sha256": self.context.context_sha256,
            "configuration_sha256": (
                self.configuration.configuration_sha256
            ),
            "registered_services": list(
                self.services.registered_ids()
            ),
            "event_count": len(self.events.history()),
            "result_sha256": (
                None if self.result is None else self.result.result_sha256
            ),
        }

    @property
    def snapshot_sha256(self) -> str:
        return stable_sha256(self.snapshot())

    def _transition(self, target: RuntimeState) -> None:
        validate_transition(self.state, target)
        self.state = target

    def _emit(
        self,
        event_type: KernelEventType,
        detail: dict[str, Any],
    ) -> None:
        self._sequence += 1
        event = KernelEvent(
            schema_version="1.0",
            session_id=self.context.session_id,
            event_type=event_type,
            sequence=self._sequence,
            occurred_utc=utc_now(),
            detail=detail,
        )
        self.events.publish(event)
