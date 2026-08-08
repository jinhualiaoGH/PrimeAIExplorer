from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError
from experimental_campaign.identity import canonical_metadata, sha256_json

from .reproducibility_contracts import ReproducibilityCertificate


@dataclass(frozen=True, slots=True)
class ReproducibilityCertificateManifest:
    certificate_id: str
    certificate_sha256: str
    campaign_id: str
    experiment_id: str
    reproducible: bool
    passed_count: int
    failed_count: int
    skipped_count: int
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "certificate_id",
            "certificate_sha256",
            "campaign_id",
            "experiment_id",
            "source",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(
                    f"{name} must be a non-empty string."
                )
            object.__setattr__(self, name, value.strip())

        if not isinstance(self.reproducible, bool):
            raise ValidationError("reproducible must be bool.")

        for name in (
            "passed_count",
            "failed_count",
            "skipped_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValidationError(
                    f"{name} must be a non-negative integer."
                )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(
            self,
            "metadata",
            canonical_metadata(self.metadata),
        )

    @classmethod
    def from_certificate(
        cls,
        certificate: ReproducibilityCertificate,
        *,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ReproducibilityCertificateManifest":
        if not isinstance(certificate, ReproducibilityCertificate):
            raise ValidationError(
                "certificate must be ReproducibilityCertificate."
            )

        return cls(
            certificate_id=certificate.certificate_id,
            certificate_sha256=certificate.certificate_sha256,
            campaign_id=certificate.campaign_id,
            experiment_id=certificate.experiment_id,
            reproducible=certificate.reproducible,
            passed_count=certificate.passed_count,
            failed_count=certificate.failed_count,
            skipped_count=certificate.skipped_count,
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "i4.0",
            "certificate_id": self.certificate_id,
            "certificate_sha256": self.certificate_sha256,
            "campaign_id": self.campaign_id,
            "experiment_id": self.experiment_id,
            "reproducible": self.reproducible,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())
