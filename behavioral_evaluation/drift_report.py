from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from kernel.exceptions import ValidationError

from .baselines import FingerprintBaselineRegistry
from .drift import BehavioralDriftReport, DriftThresholds, compare_drift
from .fingerprints import BehavioralFingerprint


@dataclass(frozen=True, slots=True)
class BehavioralDriftCampaignReport:
    baseline_id: str
    reports: tuple[BehavioralDriftReport, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g7.0",
            "baseline_id": self.baseline_id,
            "reports": [report.to_dict() for report in self.reports],
        }


def compare_to_baseline(
    registry: FingerprintBaselineRegistry,
    baseline_id: str,
    fingerprints: Iterable[BehavioralFingerprint],
    *,
    thresholds: DriftThresholds | None = None,
) -> BehavioralDriftCampaignReport:
    if not isinstance(registry, FingerprintBaselineRegistry):
        raise ValidationError(
            "registry must be FingerprintBaselineRegistry."
        )

    baseline = registry.get(baseline_id)
    values = tuple(fingerprints)
    reports = tuple(
        compare_drift(
            baseline.fingerprint,
            current,
            thresholds=thresholds,
        )
        for current in sorted(
            values,
            key=lambda item: (
                item.provider,
                item.model,
                item.fingerprint_sha256,
            ),
        )
    )

    return BehavioralDriftCampaignReport(
        baseline_id=baseline.baseline_id,
        reports=reports,
    )
