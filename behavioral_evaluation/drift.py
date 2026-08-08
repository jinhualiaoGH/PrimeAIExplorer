from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from kernel.exceptions import ValidationError

from .fingerprints import BehavioralFingerprint


@dataclass(frozen=True, slots=True)
class DriftThresholds:
    stable_max: float = 0.05
    minor_max: float = 0.15
    material_max: float = 0.30

    def __post_init__(self) -> None:
        values = (
            self.stable_max,
            self.minor_max,
            self.material_max,
        )
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
            for value in values
        ):
            raise ValidationError(
                "drift thresholds must be nonnegative numbers."
            )
        if not (
            self.stable_max
            <= self.minor_max
            <= self.material_max
        ):
            raise ValidationError(
                "drift thresholds must be monotonically increasing."
            )

    def classify(self, score: float) -> str:
        if score <= self.stable_max:
            return "stable"
        if score <= self.minor_max:
            return "minor"
        if score <= self.material_max:
            return "material"
        return "major"

    def to_dict(self) -> dict[str, float | str]:
        return {
            "schema_version": "g7.0",
            **asdict(self),
        }


@dataclass(frozen=True, slots=True)
class FeatureDrift:
    name: str
    baseline_value: float | None
    current_value: float | None
    delta: float | None
    absolute_delta: float | None
    direction: str
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g7.0",
            **asdict(self),
        }


@dataclass(frozen=True, slots=True)
class BehavioralDriftReport:
    baseline_fingerprint_sha256: str
    current_fingerprint_sha256: str
    provider: str
    baseline_model: str
    current_model: str
    comparable_features: int
    aggregate_drift_score: float | None
    classification: str
    features: tuple[FeatureDrift, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g7.0",
            "baseline_fingerprint_sha256": self.baseline_fingerprint_sha256,
            "current_fingerprint_sha256": self.current_fingerprint_sha256,
            "provider": self.provider,
            "baseline_model": self.baseline_model,
            "current_model": self.current_model,
            "comparable_features": self.comparable_features,
            "aggregate_drift_score": self.aggregate_drift_score,
            "classification": self.classification,
            "features": [feature.to_dict() for feature in self.features],
        }


def _interpret(delta: float | None, direction: str) -> str:
    if delta is None:
        return "not_comparable"
    if abs(delta) <= 1e-15:
        return "unchanged"
    if direction == "neutral":
        return "changed"
    # G6 vectors are direction-oriented: larger normalized value is better.
    return "improvement" if delta > 0 else "degradation"


def compare_drift(
    baseline: BehavioralFingerprint,
    current: BehavioralFingerprint,
    *,
    thresholds: DriftThresholds | None = None,
) -> BehavioralDriftReport:
    if not isinstance(baseline, BehavioralFingerprint):
        raise ValidationError("baseline must be BehavioralFingerprint.")
    if not isinstance(current, BehavioralFingerprint):
        raise ValidationError("current must be BehavioralFingerprint.")
    if baseline.schema_sha256 != current.schema_sha256:
        raise ValidationError(
            "Drift comparison requires identical fingerprint schemas."
        )
    if len(baseline.features) != len(current.features):
        raise ValidationError("Fingerprint feature lengths differ.")

    thresholds = thresholds or DriftThresholds()
    features: list[FeatureDrift] = []
    squared = []

    for left, right in zip(baseline.features, current.features):
        if left.name != right.name:
            raise ValidationError(
                "Fingerprint feature ordering differs."
            )
        if left.direction != right.direction:
            raise ValidationError(
                f"Fingerprint direction differs for {left.name}."
            )

        if (
            left.normalized_value is None
            or right.normalized_value is None
        ):
            delta = None
            absolute_delta = None
        else:
            delta = (
                float(right.normalized_value)
                - float(left.normalized_value)
            )
            absolute_delta = abs(delta)
            squared.append(delta * delta)

        features.append(
            FeatureDrift(
                name=left.name,
                baseline_value=left.normalized_value,
                current_value=right.normalized_value,
                delta=delta,
                absolute_delta=absolute_delta,
                direction=left.direction,
                interpretation=_interpret(delta, left.direction),
            )
        )

    if not squared:
        score = None
        classification = "not_comparable"
    else:
        # Root-mean-square feature movement keeps score dimension independent.
        score = math.sqrt(sum(squared) / len(squared))
        classification = thresholds.classify(score)

    provider = (
        baseline.provider
        if baseline.provider == current.provider
        else f"{baseline.provider}->{current.provider}"
    )

    return BehavioralDriftReport(
        baseline_fingerprint_sha256=baseline.fingerprint_sha256,
        current_fingerprint_sha256=current.fingerprint_sha256,
        provider=provider,
        baseline_model=baseline.model,
        current_model=current.model,
        comparable_features=len(squared),
        aggregate_drift_score=score,
        classification=classification,
        features=tuple(features),
    )
