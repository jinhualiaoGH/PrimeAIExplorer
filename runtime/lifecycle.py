from __future__ import annotations

from enum import Enum

from kernel.exceptions import ValidationError


class RuntimeState(str, Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CLOSED = "closed"


_ALLOWED_TRANSITIONS: dict[RuntimeState, set[RuntimeState]] = {
    RuntimeState.CREATED: {
        RuntimeState.INITIALIZED,
        RuntimeState.FAILED,
        RuntimeState.CLOSED,
    },
    RuntimeState.INITIALIZED: {
        RuntimeState.RUNNING,
        RuntimeState.FAILED,
        RuntimeState.CLOSED,
    },
    RuntimeState.RUNNING: {
        RuntimeState.FINISHED,
        RuntimeState.FAILED,
    },
    RuntimeState.FINISHED: {
        RuntimeState.CLOSED,
    },
    RuntimeState.FAILED: {
        RuntimeState.CLOSED,
    },
    RuntimeState.CLOSED: set(),
}


def validate_transition(
    current: RuntimeState,
    target: RuntimeState,
) -> None:
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ValidationError(
            f"Invalid runtime transition: {current.value} -> {target.value}"
        )
