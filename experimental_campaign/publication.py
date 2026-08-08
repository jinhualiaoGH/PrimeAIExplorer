from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from kernel.exceptions import ValidationError

from .analysis_contracts import CampaignAnalysisReport
from .identity import canonical_metadata, sha256_json
from .integration import ScientificIntegrationRecord
from .validation import require_text


class ObservatoryPublisher(Protocol):
    def __call__(
        self,
        analysis_report: CampaignAnalysisReport,
        integration: ScientificIntegrationRecord,
    ) -> Any:
        ...


def _canonical_external_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_external_payload(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_external_payload(item) for item in value]

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _canonical_external_payload(value.to_dict())

    if hasattr(value, "__dict__"):
        return _canonical_external_payload(vars(value))

    return str(value)


@dataclass(frozen=True, slots=True)
class BehavioralObservatoryPublication:
    publication_id: str
    integration_id: str
    integration_sha256: str
    report_id: str
    report_sha256: str
    observatory_payload: Any
    publisher_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "publication_id",
            "integration_id",
            "integration_sha256",
            "report_id",
            "report_sha256",
            "publisher_id",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        object.__setattr__(
            self,
            "observatory_payload",
            _canonical_external_payload(self.observatory_payload),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h8.0",
            "integration_id": self.integration_id,
            "integration_sha256": self.integration_sha256,
            "report_id": self.report_id,
            "report_sha256": self.report_sha256,
            "observatory_payload": self.observatory_payload,
            "publisher_id": self.publisher_id,
            "metadata": dict(self.metadata),
        }

    @property
    def publication_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["publication_id"] = self.publication_id
        payload["publication_sha256"] = self.publication_sha256
        return payload


@dataclass(frozen=True, slots=True)
class CampaignObservatoryPublisher:
    publisher: ObservatoryPublisher | Callable[[CampaignAnalysisReport, ScientificIntegrationRecord], Any]
    publisher_id: str = "phase-g8.observatory"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not callable(self.publisher):
            raise ValidationError("publisher must be callable.")
        object.__setattr__(
            self,
            "publisher_id",
            require_text("publisher_id", self.publisher_id),
        )
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def publish(
        self,
        *,
        analysis_report: CampaignAnalysisReport,
        integration: ScientificIntegrationRecord,
        metadata: Mapping[str, Any] | None = None,
    ) -> BehavioralObservatoryPublication:
        if not isinstance(analysis_report, CampaignAnalysisReport):
            raise ValidationError("analysis_report must be CampaignAnalysisReport.")
        if not isinstance(integration, ScientificIntegrationRecord):
            raise ValidationError("integration must be ScientificIntegrationRecord.")

        if integration.analysis_report_id != analysis_report.report_id:
            raise ValidationError("integration/report ID mismatch.")
        if integration.analysis_report_sha256 != analysis_report.report_sha256:
            raise ValidationError("integration/report SHA-256 mismatch.")

        payload = self.publisher(analysis_report, integration)
        canonical_payload = _canonical_external_payload(payload)

        seed = {
            "schema_version": "h8.0",
            "integration_sha256": integration.integration_sha256,
            "report_sha256": analysis_report.report_sha256,
            "observatory_payload": canonical_payload,
            "publisher_id": self.publisher_id,
        }

        return BehavioralObservatoryPublication(
            publication_id=f"PUBLICATION-{sha256_json(seed)[:20].upper()}",
            integration_id=integration.integration_id,
            integration_sha256=integration.integration_sha256,
            report_id=analysis_report.report_id,
            report_sha256=analysis_report.report_sha256,
            observatory_payload=canonical_payload,
            publisher_id=self.publisher_id,
            metadata={
                **dict(self.metadata),
                **dict(metadata or {}),
            },
        )
