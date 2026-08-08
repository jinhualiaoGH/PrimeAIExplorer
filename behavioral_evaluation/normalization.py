from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from kernel.exceptions import ValidationError

from .fingerprints import FingerprintSchema


def _finite(value: float | int | None) -> float | None:
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value):
        raise ValidationError("Fingerprint metrics must be finite.")
    return value


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def bounded_normalize(
    value: float | int | None,
    lower: float | None,
    upper: float | None,
) -> float | None:
    value = _finite(value)
    if value is None:
        return None

    if lower is None and upper is None:
        return value

    if lower is not None and upper is not None:
        if upper <= lower:
            raise ValidationError("upper bound must be greater than lower bound.")
        return clamp01((value - lower) / (upper - lower))

    if lower is not None:
        shifted = max(0.0, value - lower)
        return shifted / (1.0 + shifted)

    assert upper is not None
    shifted = max(0.0, upper - value)
    return shifted / (1.0 + shifted)


def orient_normalized_value(
    normalized: float | None,
    direction: str,
) -> float | None:
    if normalized is None:
        return None
    if direction == "higher_is_better":
        return normalized
    if direction == "lower_is_better":
        return 1.0 - normalized
    if direction == "neutral":
        return normalized
    raise ValidationError(f"Unknown metric direction: {direction}")


@dataclass(frozen=True, slots=True)
class FingerprintNormalizer:
    schema: FingerprintSchema

    def normalize_metric(
        self,
        name: str,
        value: float | int | None,
    ) -> float | None:
        if name not in self.schema.feature_names:
            raise ValidationError(f"Unknown fingerprint feature: {name}")

        lower, upper = self.schema.bounds[name]
        base = bounded_normalize(value, lower, upper)
        return orient_normalized_value(
            base,
            self.schema.directions[name],
        )

    def normalize_map(
        self,
        raw_metrics: Mapping[str, float | int | None],
    ) -> tuple[float | None, ...]:
        missing = [
            name
            for name in self.schema.feature_names
            if name not in raw_metrics
        ]
        if missing:
            raise ValidationError(
                "Missing raw fingerprint metrics: " + ", ".join(missing)
            )

        return tuple(
            self.normalize_metric(name, raw_metrics[name])
            for name in self.schema.feature_names
        )
