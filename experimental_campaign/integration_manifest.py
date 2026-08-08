from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .integration import ScientificIntegrationRecord
from .publication import BehavioralObservatoryPublication
from .validation import require_text


@dataclass(frozen=True, slots=True)
class ScientificIntegrationManifest:
    integration_id: str
    integration_sha256: str
    result_set_id: str
    result_set_sha256: str
    provenance_sha256: str
    analysis_report_id: str
    analysis_report_sha256: str
    publication_id: str
    publication_sha256: str
    publisher_id: str
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "integration_id",
            "integration_sha256",
            "result_set_id",
            "result_set_sha256",
            "provenance_sha256",
            "analysis_report_id",
            "analysis_report_sha256",
            "publication_id",
            "publication_sha256",
            "publisher_id",
            "source",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @classmethod
    def build(
        cls,
        *,
        integration: ScientificIntegrationRecord,
        publication: BehavioralObservatoryPublication,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ScientificIntegrationManifest":
        if not isinstance(integration, ScientificIntegrationRecord):
            raise ValidationError("integration must be ScientificIntegrationRecord.")
        if not isinstance(publication, BehavioralObservatoryPublication):
            raise ValidationError("publication must be BehavioralObservatoryPublication.")

        if publication.integration_id != integration.integration_id:
            raise ValidationError("publication integration_id mismatch.")
        if publication.integration_sha256 != integration.integration_sha256:
            raise ValidationError("publication integration_sha256 mismatch.")
        if publication.report_id != integration.analysis_report_id:
            raise ValidationError("publication report_id mismatch.")
        if publication.report_sha256 != integration.analysis_report_sha256:
            raise ValidationError("publication report_sha256 mismatch.")

        return cls(
            integration_id=integration.integration_id,
            integration_sha256=integration.integration_sha256,
            result_set_id=integration.result_set_id,
            result_set_sha256=integration.result_set_sha256,
            provenance_sha256=integration.provenance_sha256,
            analysis_report_id=integration.analysis_report_id,
            analysis_report_sha256=integration.analysis_report_sha256,
            publication_id=publication.publication_id,
            publication_sha256=publication.publication_sha256,
            publisher_id=publication.publisher_id,
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h8.0",
            "integration_id": self.integration_id,
            "integration_sha256": self.integration_sha256,
            "result_set_id": self.result_set_id,
            "result_set_sha256": self.result_set_sha256,
            "provenance_sha256": self.provenance_sha256,
            "analysis_report_id": self.analysis_report_id,
            "analysis_report_sha256": self.analysis_report_sha256,
            "publication_id": self.publication_id,
            "publication_sha256": self.publication_sha256,
            "publisher_id": self.publisher_id,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())
