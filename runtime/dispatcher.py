from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from kernel.events import KernelEvent
from kernel.exceptions import ConfigurationError, RunnerError


EventHandler = Callable[[KernelEvent], None]


@dataclass
class EventBus:
    _handlers: dict[str, list[EventHandler]] = field(default_factory=dict)
    _history: list[KernelEvent] = field(default_factory=list)

    def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
    ) -> None:
        normalized = self._normalize_name(event_name)
        if not callable(handler):
            raise ConfigurationError("Event handler must be callable.")
        self._handlers.setdefault(normalized, [])
        if handler in self._handlers[normalized]:
            raise ConfigurationError(
                f"Handler already subscribed to event: {normalized}"
            )
        self._handlers[normalized].append(handler)

    def unsubscribe(
        self,
        event_name: str,
        handler: EventHandler,
    ) -> None:
        normalized = self._normalize_name(event_name)
        handlers = self._handlers.get(normalized, [])
        if handler not in handlers:
            raise ConfigurationError(
                f"Handler is not subscribed to event: {normalized}"
            )
        handlers.remove(handler)

    def publish(self, event: KernelEvent) -> None:
        self._history.append(event)
        event_name = event.event_type.value
        failures = []
        for handler in tuple(self._handlers.get(event_name, ())):
            try:
                handler(event)
            except Exception as exc:
                failures.append(exc)
        if failures:
            raise RunnerError(
                f"{len(failures)} event handler(s) failed for {event_name}."
            ) from failures[0]

    def history(self) -> tuple[KernelEvent, ...]:
        return tuple(self._history)

    @staticmethod
    def _normalize_name(event_name: str) -> str:
        if not isinstance(event_name, str):
            raise ConfigurationError("event_name must be text.")
        normalized = event_name.strip()
        if not normalized:
            raise ConfigurationError("event_name must not be empty.")
        return normalized
