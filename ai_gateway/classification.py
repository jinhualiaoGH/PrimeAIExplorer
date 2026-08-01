from __future__ import annotations


_TRANSIENT_MARKERS = (
    "http 408",
    "http 409",
    "http 425",
    "http 429",
    "http 500",
    "http 502",
    "http 503",
    "http 504",
    "rate limit",
    "temporarily unavailable",
    "timeout",
    "timed out",
    "transport failure",
    "connection reset",
)


def is_transient_error(error: BaseException) -> bool:
    text = f"{type(error).__name__}: {error}".lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)
