from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from kernel.exceptions import ValidationError


def require_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be non-empty text.")
    return value.strip()


def optional_text(name: str, value: Any) -> str | None:
    if value is None:
        return None
    return require_text(name, value)


def require_positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{name} must be a positive integer.")
    return value


def require_probability(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be numeric.")
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValidationError(f"{name} must be in [0, 1].")
    return number
