from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .aggregation import ProviderBehaviorMetrics
from .fingerprints import (
    DEFAULT_FINGERPRINT_SCHEMA,
    BehavioralFingerprint,
    FingerprintFeature,
    FingerprintSchema,
    raw_metric_map,
    sha256_json,
)
from .normalization import FingerprintNormalizer


@dataclass(frozen=True, slots=True)
class FingerprintBuilder:
    schema: FingerprintSchema = DEFAULT_FINGERPRINT_SCHEMA

    def build(
        self,
        metrics: ProviderBehaviorMetrics,
        *,
        provenance: Mapping[str, Any] | None = None,
    ) -> BehavioralFingerprint:
        raw_metrics = raw_metric_map(metrics)
        normalizer = FingerprintNormalizer(self.schema)
        vector = normalizer.normalize_map(raw_metrics)

        features = tuple(
            FingerprintFeature(
                name=name,
                raw_value=(
                    None
                    if raw_metrics[name] is None
                    else float(raw_metrics[name])
                ),
                normalized_value=vector[index],
                direction=self.schema.directions[name],
                lower_bound=self.schema.bounds[name][0],
                upper_bound=self.schema.bounds[name][1],
            )
            for index, name in enumerate(self.schema.feature_names)
        )

        payload = {
            "schema_version": "g6.0",
            "schema_id": self.schema.schema_id,
            "schema_sha256": self.schema.schema_sha256,
            "provider": metrics.provider,
            "model": metrics.model,
            "observations": metrics.observations,
            "evaluated": metrics.evaluated,
            "raw_metrics": raw_metrics,
            "features": [feature.to_dict() for feature in features],
            "vector": list(vector),
            "provenance": dict(provenance or {}),
        }
        fingerprint_sha256 = sha256_json(payload)

        return BehavioralFingerprint(
            schema_id=self.schema.schema_id,
            schema_sha256=self.schema.schema_sha256,
            provider=metrics.provider,
            model=metrics.model,
            observations=metrics.observations,
            evaluated=metrics.evaluated,
            raw_metrics=raw_metrics,
            features=features,
            vector=vector,
            provenance=dict(provenance or {}),
            fingerprint_sha256=fingerprint_sha256,
        )
