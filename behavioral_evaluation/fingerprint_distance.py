from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from kernel.exceptions import ValidationError

from .fingerprints import BehavioralFingerprint


def _paired_values(
    left: BehavioralFingerprint,
    right: BehavioralFingerprint,
) -> tuple[tuple[float, float], ...]:
    if left.schema_sha256 != right.schema_sha256:
        raise ValidationError(
            "Fingerprints must use the same schema before comparison."
        )
    if len(left.vector) != len(right.vector):
        raise ValidationError("Fingerprint vector lengths differ.")

    return tuple(
        (float(a), float(b))
        for a, b in zip(left.vector, right.vector)
        if a is not None and b is not None
    )


def euclidean_distance(
    left: BehavioralFingerprint,
    right: BehavioralFingerprint,
) -> float | None:
    pairs = _paired_values(left, right)
    if not pairs:
        return None
    return math.sqrt(sum((a - b) ** 2 for a, b in pairs))


def manhattan_distance(
    left: BehavioralFingerprint,
    right: BehavioralFingerprint,
) -> float | None:
    pairs = _paired_values(left, right)
    if not pairs:
        return None
    return sum(abs(a - b) for a, b in pairs)


def cosine_similarity(
    left: BehavioralFingerprint,
    right: BehavioralFingerprint,
) -> float | None:
    pairs = _paired_values(left, right)
    if not pairs:
        return None

    dot = sum(a * b for a, b in pairs)
    left_norm = math.sqrt(sum(a * a for a, _ in pairs))
    right_norm = math.sqrt(sum(b * b for _, b in pairs))

    if left_norm == 0.0 or right_norm == 0.0:
        return None

    return dot / (left_norm * right_norm)


@dataclass(frozen=True, slots=True)
class FingerprintComparison:
    provider_a: str
    model_a: str
    provider_b: str
    model_b: str
    comparable_features: int
    euclidean_distance: float | None
    manhattan_distance: float | None
    cosine_similarity: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g6.0",
            **asdict(self),
        }


def compare_fingerprints(
    left: BehavioralFingerprint,
    right: BehavioralFingerprint,
) -> FingerprintComparison:
    pairs = _paired_values(left, right)
    return FingerprintComparison(
        provider_a=left.provider,
        model_a=left.model,
        provider_b=right.provider,
        model_b=right.model,
        comparable_features=len(pairs),
        euclidean_distance=euclidean_distance(left, right),
        manhattan_distance=manhattan_distance(left, right),
        cosine_similarity=cosine_similarity(left, right),
    )
