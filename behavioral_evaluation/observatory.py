from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256

from .aggregation import BehavioralMetricsReport
from .comparison_matrix import FingerprintComparisonMatrix, build_comparison_matrix
from .drift_report import BehavioralDriftCampaignReport
from .fingerprints import BehavioralFingerprint


@dataclass(frozen=True, slots=True)
class BehavioralObservatorySnapshot:
    """Immutable G8 presentation snapshot built from frozen G5-G7 artifacts."""

    snapshot_id: str
    metrics_report: BehavioralMetricsReport
    fingerprints: tuple[BehavioralFingerprint, ...]
    comparison_matrix: FingerprintComparisonMatrix
    drift_reports: tuple[BehavioralDriftCampaignReport, ...]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot_id, str) or not self.snapshot_id.strip():
            raise ValidationError("snapshot_id must be non-empty text.")
        if not isinstance(self.metrics_report, BehavioralMetricsReport):
            raise ValidationError("metrics_report must be BehavioralMetricsReport.")
        if not isinstance(self.comparison_matrix, FingerprintComparisonMatrix):
            raise ValidationError(
                "comparison_matrix must be FingerprintComparisonMatrix."
            )

        fingerprints = tuple(self.fingerprints)
        drift_reports = tuple(self.drift_reports)

        for item in fingerprints:
            if not isinstance(item, BehavioralFingerprint):
                raise ValidationError(
                    "fingerprints must contain BehavioralFingerprint values."
                )
        for item in drift_reports:
            if not isinstance(item, BehavioralDriftCampaignReport):
                raise ValidationError(
                    "drift_reports must contain BehavioralDriftCampaignReport values."
                )
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")

        subjects = tuple(
            sorted(f"{item.provider}/{item.model}" for item in fingerprints)
        )
        if subjects != self.comparison_matrix.subjects:
            raise ValidationError(
                "comparison_matrix subjects do not match fingerprints."
            )

        object.__setattr__(self, "snapshot_id", self.snapshot_id.strip())
        object.__setattr__(
            self,
            "fingerprints",
            tuple(
                sorted(
                    fingerprints,
                    key=lambda item: (
                        item.provider,
                        item.model,
                        item.fingerprint_sha256,
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "drift_reports",
            tuple(
                sorted(
                    drift_reports,
                    key=lambda item: item.baseline_id,
                )
            ),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g8.0",
            "snapshot_id": self.snapshot_id,
            "metrics_report": self.metrics_report.to_dict(),
            "fingerprints": [
                fingerprint.to_dict()
                for fingerprint in self.fingerprints
            ],
            "comparison_matrix": self.comparison_matrix.to_dict(),
            "drift_reports": [
                report.to_dict()
                for report in self.drift_reports
            ],
            "metadata": dict(self.metadata),
        }

    @property
    def snapshot_sha256(self) -> str:
        return stable_sha256(self.to_dict())


def build_observatory_snapshot(
    *,
    snapshot_id: str,
    metrics_report: BehavioralMetricsReport,
    fingerprints: Iterable[BehavioralFingerprint],
    drift_reports: Iterable[BehavioralDriftCampaignReport] = (),
    metadata: Mapping[str, Any] | None = None,
) -> BehavioralObservatorySnapshot:
    fingerprints = tuple(fingerprints)
    matrix = build_comparison_matrix(fingerprints)

    return BehavioralObservatorySnapshot(
        snapshot_id=snapshot_id,
        metrics_report=metrics_report,
        fingerprints=fingerprints,
        comparison_matrix=matrix,
        drift_reports=tuple(drift_reports),
        metadata=dict(metadata or {}),
    )
