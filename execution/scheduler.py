from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from execution.models import ExecutionRequest
from kernel.exceptions import ConfigurationError


@dataclass
class ExecutionScheduler:
    _queue: deque[ExecutionRequest] = field(default_factory=deque)
    _execution_ids: set[str] = field(default_factory=set)

    def submit(self, request: ExecutionRequest) -> None:
        if request.execution_id in self._execution_ids:
            raise ConfigurationError(
                f"Duplicate execution_id: {request.execution_id}"
            )
        self._queue.append(request)
        self._execution_ids.add(request.execution_id)

    def next_request(self) -> ExecutionRequest:
        if not self._queue:
            raise ConfigurationError("Execution queue is empty.")
        request = self._queue.popleft()
        self._execution_ids.remove(request.execution_id)
        return request

    def pending_count(self) -> int:
        return len(self._queue)

    def pending_ids(self) -> tuple[str, ...]:
        return tuple(request.execution_id for request in self._queue)

    def clear(self) -> tuple[ExecutionRequest, ...]:
        removed = tuple(self._queue)
        self._queue.clear()
        self._execution_ids.clear()
        return removed
