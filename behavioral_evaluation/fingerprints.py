from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from kernel.exceptions import ValidationError

from .aggregation import ProviderBehaviorMetrics


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class FingerprintFeature:
    name: str
    raw_value: float | None
    normalized_value: float | None
    direction: str
    lower_bound: float | None = None
    upper_bound: float | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValidationError("FingerprintFeature.name is required.")
        if self.direction not in {"higher_is_better", "lower_is_better", "neutral"}:
            raise ValidationError(
                "FingerprintFeature.direction must be higher_is_better, "
                "lower_is_better, or neutral."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FingerprintSchema:
    schema_id: str
    feature_names: tuple[str, ...]
    directions: Mapping[str, str]
    bounds: Mapping[str, tuple[float | None, float | None]]

    def __post_init__(self) -> None:
        if not self.schema_id:
            raise ValidationError("FingerprintSchema.schema_id is required.")
        if not self.feature_names:
            raise ValidationError(
                "FingerprintSchema requires at least one feature."
            )
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValidationError("FingerprintSchema.feature_names must be unique.")

        for name in self.feature_names:
            if name not in self.directions:
                raise ValidationError(f"Missing direction for feature: {name}")
            direction = self.directions[name]
            if direction not in {
                "higher_is_better",
                "lower_is_better",
                "neutral",
            }:
                raise ValidationError(
                    f"Invalid direction for feature {name}: {direction}"
                )
            if name not in self.bounds:
                raise ValidationError(f"Missing bounds for feature: {name}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g6.0",
            "schema_id": self.schema_id,
            "feature_names": list(self.feature_names),
            "directions": dict(self.directions),
            "bounds": {
                key: [value[0], value[1]]
                for key, value in self.bounds.items()
            },
        }

    @property
    def schema_sha256(self) -> str:
        return sha256_json(self.to_dict())


DEFAULT_FINGERPRINT_SCHEMA = FingerprintSchema(
    schema_id="behavioral-fingerprint.g6.default",
    feature_names=(
        "pass_rate_pct",
        "mean_score",
        "provider_error_rate_pct",
        "calibration_error_pct",
        "mean_case_surface_consistency_pct",
        "mean_case_semantic_consistency_pct",
        "mean_case_surface_entropy_bits",
        "mean_case_semantic_entropy_bits",
        "median_latency_seconds",
        "p95_latency_seconds",
        "latency_tail_ratio",
        "mean_tokens",
        "token_efficiency",
    ),
    directions={
        "pass_rate_pct": "higher_is_better",
        "mean_score": "higher_is_better",
        "provider_error_rate_pct": "lower_is_better",
        "calibration_error_pct": "lower_is_better",
        "mean_case_surface_consistency_pct": "higher_is_better",
        "mean_case_semantic_consistency_pct": "higher_is_better",
        "mean_case_surface_entropy_bits": "lower_is_better",
        "mean_case_semantic_entropy_bits": "lower_is_better",
        "median_latency_seconds": "lower_is_better",
        "p95_latency_seconds": "lower_is_better",
        "latency_tail_ratio": "lower_is_better",
        "mean_tokens": "lower_is_better",
        "token_efficiency": "higher_is_better",
    },
    bounds={
        "pass_rate_pct": (0.0, 100.0),
        "mean_score": (0.0, 100.0),
        "provider_error_rate_pct": (0.0, 100.0),
        "calibration_error_pct": (0.0, 100.0),
        "mean_case_surface_consistency_pct": (0.0, 100.0),
        "mean_case_semantic_consistency_pct": (0.0, 100.0),
        "mean_case_surface_entropy_bits": (0.0, None),
        "mean_case_semantic_entropy_bits": (0.0, None),
        "median_latency_seconds": (0.0, None),
        "p95_latency_seconds": (0.0, None),
        "latency_tail_ratio": (0.0, None),
        "mean_tokens": (0.0, None),
        "token_efficiency": (0.0, None),
    },
)


@dataclass(frozen=True, slots=True)
class BehavioralFingerprint:
    schema_id: str
    schema_sha256: str
    provider: str
    model: str
    observations: int
    evaluated: int
    raw_metrics: Mapping[str, float | int | None]
    features: tuple[FingerprintFeature, ...]
    vector: tuple[float | None, ...]
    provenance: Mapping[str, Any]
    fingerprint_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g6.0",
            "schema_id": self.schema_id,
            "schema_sha256": self.schema_sha256,
            "provider": self.provider,
            "model": self.model,
            "observations": self.observations,
            "evaluated": self.evaluated,
            "raw_metrics": dict(self.raw_metrics),
            "features": [feature.to_dict() for feature in self.features],
            "vector": list(self.vector),
            "provenance": dict(self.provenance),
            "fingerprint_sha256": self.fingerprint_sha256,
        }

    def identity_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("fingerprint_sha256")
        return payload

    def verify_identity(self) -> bool:
        return sha256_json(self.identity_payload()) == self.fingerprint_sha256


def raw_metric_map(metrics: ProviderBehaviorMetrics) -> dict[str, float | int | None]:
    data = metrics.to_dict()
    data.pop("schema_version", None)
    data.pop("provider", None)
    data.pop("model", None)
    return data
