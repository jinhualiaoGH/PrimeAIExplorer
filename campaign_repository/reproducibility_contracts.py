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


class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class EvidenceIdentity:
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
            _require_text("sha256", self.sha256),
        )
        if len(self.sha256) != 64 or any(
            char not in "0123456789abcdefABCDEF"
            for char in self.sha256
        ):
            raise ValidationError(
                "sha256 must be a 64-character hexadecimal digest."
            )
        object.__setattr__(self, "sha256", self.sha256.lower())

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
class VerificationCheck:
    check_id: str
    status: VerificationStatus
    message: str
    evidence: tuple[EvidenceIdentity, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "check_id",
            _require_text("check_id", self.check_id),
        )
        object.__setattr__(
            self,
            "message",
            _require_text("message", self.message),
        )

        if not isinstance(self.status, VerificationStatus):
            try:
                object.__setattr__(
                    self,
                    "status",
                    VerificationStatus(self.status),
                )
            except Exception as exc:
                raise ValidationError(
                    "invalid verification status."
                ) from exc

        evidence = tuple(self.evidence)
        if any(
            not isinstance(item, EvidenceIdentity)
            for item in evidence
        ):
            raise ValidationError(
                "evidence must contain EvidenceIdentity values."
            )
        keys = [
            (item.evidence_type, item.evidence_id, item.sha256)
            for item in evidence
        ]
        if len(keys) != len(set(keys)):
            raise ValidationError(
                "verification check contains duplicate evidence identities."
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
    def passed(self) -> bool:
        return self.status == VerificationStatus.PASSED

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status.value,
            "message": self.message,
            "evidence": [item.to_dict() for item in self.evidence],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ReproducibilityCertificate:
    certificate_id: str
    campaign_id: str
    experiment_id: str
    checks: tuple[VerificationCheck, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "certificate_id",
            "campaign_id",
            "experiment_id",
        ):
            object.__setattr__(
                self,
                name,
                _require_text(name, getattr(self, name)),
            )

        checks = tuple(self.checks)
        if any(
            not isinstance(item, VerificationCheck)
            for item in checks
        ):
            raise ValidationError(
                "checks must contain VerificationCheck values."
            )

        ids = [item.check_id for item in checks]
        if len(ids) != len(set(ids)):
            raise ValidationError(
                "certificate contains duplicate check IDs."
            )

        object.__setattr__(
            self,
            "checks",
            tuple(sorted(checks, key=lambda item: item.check_id)),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(
            self,
            "metadata",
            canonical_metadata(self.metadata),
        )

    @property
    def passed_count(self) -> int:
        return sum(
            item.status == VerificationStatus.PASSED
            for item in self.checks
        )

    @property
    def failed_count(self) -> int:
        return sum(
            item.status == VerificationStatus.FAILED
            for item in self.checks
        )

    @property
    def skipped_count(self) -> int:
        return sum(
            item.status == VerificationStatus.SKIPPED
            for item in self.checks
        )

    @property
    def reproducible(self) -> bool:
        return self.failed_count == 0

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "i4.0",
            "campaign_id": self.campaign_id,
            "experiment_id": self.experiment_id,
            "checks": [item.to_dict() for item in self.checks],
            "metadata": dict(self.metadata),
        }

    @property
    def certificate_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "certificate_id": self.certificate_id,
                "certificate_sha256": self.certificate_sha256,
                "passed_count": self.passed_count,
                "failed_count": self.failed_count,
                "skipped_count": self.skipped_count,
                "reproducible": self.reproducible,
            }
        )
        return payload
