from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from kernel.exceptions import ValidationError
from experimental_campaign.identity import canonical_metadata, sha256_json


def _require_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be a non-empty string.")
    return value.strip()


def _require_sha256(name: str, value: str) -> str:
    value = _require_text(name, value).lower()
    if len(value) != 64 or any(
        char not in "0123456789abcdef"
        for char in value
    ):
        raise ValidationError(
            f"{name} must be a 64-character hexadecimal digest."
        )
    return value


class CatalogTrustStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


@dataclass(frozen=True, slots=True)
class CatalogEvidenceRef:
    evidence_type: str
    evidence_id: str
    sha256: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_type",
            _require_text("evidence_type", self.evidence_type),
        )
        object.__setattr__(
            self,
            "evidence_id",
            _require_text("evidence_id", self.evidence_id),
        )
        object.__setattr__(
            self,
            "sha256",
            _require_sha256("sha256", self.sha256),
        )
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(
            self,
            "metadata",
            canonical_metadata(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_type": self.evidence_type,
            "evidence_id": self.evidence_id,
            "sha256": self.sha256,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ScientificReleaseCatalogRecord:
    release_id: str
    release_name: str
    campaign_id: str
    experiment_id: str
    release_manifest_sha256: str
    bundle_sha256: str
    import_path: str
    trust_status: CatalogTrustStatus
    component_kinds: tuple[str, ...] = ()
    evidence: tuple[CatalogEvidenceRef, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "release_id",
            "release_name",
            "campaign_id",
            "experiment_id",
            "import_path",
        ):
            object.__setattr__(
                self,
                name,
                _require_text(name, getattr(self, name)),
            )

        object.__setattr__(
            self,
            "release_manifest_sha256",
            _require_sha256(
                "release_manifest_sha256",
                self.release_manifest_sha256,
            ),
        )
        object.__setattr__(
            self,
            "bundle_sha256",
            _require_sha256(
                "bundle_sha256",
                self.bundle_sha256,
            ),
        )

        if not isinstance(self.trust_status, CatalogTrustStatus):
            try:
                object.__setattr__(
                    self,
                    "trust_status",
                    CatalogTrustStatus(self.trust_status),
                )
            except Exception as exc:
                raise ValidationError(
                    "invalid catalog trust status."
                ) from exc

        kinds = tuple(
            sorted(
                {
                    _require_text("component_kind", item)
                    for item in self.component_kinds
                }
            )
        )
        object.__setattr__(self, "component_kinds", kinds)

        evidence = tuple(self.evidence)
        if any(
            not isinstance(item, CatalogEvidenceRef)
            for item in evidence
        ):
            raise ValidationError(
                "evidence must contain CatalogEvidenceRef values."
            )
        keys = [
            (item.evidence_type, item.evidence_id, item.sha256)
            for item in evidence
        ]
        if len(keys) != len(set(keys)):
            raise ValidationError(
                "catalog record contains duplicate evidence references."
            )
        object.__setattr__(
            self,
            "evidence",
            tuple(
                sorted(
                    evidence,
                    key=lambda item: (
                        item.evidence_type,
                        item.evidence_id,
                        item.sha256,
                    ),
                )
            ),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(
            self,
            "metadata",
            canonical_metadata(self.metadata),
        )

    @property
    def verified(self) -> bool:
        return self.trust_status == CatalogTrustStatus.VERIFIED

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "i7.0",
            "release_id": self.release_id,
            "release_name": self.release_name,
            "campaign_id": self.campaign_id,
            "experiment_id": self.experiment_id,
            "release_manifest_sha256": self.release_manifest_sha256,
            "bundle_sha256": self.bundle_sha256,
            "import_path": self.import_path,
            "trust_status": self.trust_status.value,
            "component_kinds": list(self.component_kinds),
            "evidence": [item.to_dict() for item in self.evidence],
            "metadata": dict(self.metadata),
        }

    @property
    def record_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["record_sha256"] = self.record_sha256
        payload["verified"] = self.verified
        return payload
