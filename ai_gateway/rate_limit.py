from __future__ import annotations

import threading
import time


class FixedIntervalLimiter:
    """Thread-safe minimum-interval limiter used at the gateway boundary."""

    def __init__(
        self,
        requests_per_second: float | None = None,
        *,
        clock=time.monotonic,
        sleep=time.sleep,
    ) -> None:
        if requests_per_second is not None and requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive.")
        self.minimum_interval = (
            0.0
            if requests_per_second is None
            else 1.0 / requests_per_second
        )
        self.clock = clock
        self.sleep = sleep
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def acquire(self) -> None:
        if self.minimum_interval == 0:
            return

        with self._lock:
            now = self.clock()
            delay = max(0.0, self._next_allowed - now)
            if delay:
                self.sleep(delay)
                now = self.clock()
            self._next_allowed = max(now, self._next_allowed) + self.minimum_interval
