from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .catalog_contracts import (
    CatalogEvidenceRef,
    CatalogTrustStatus,
    ScientificReleaseCatalogRecord,
)
from .release_import import ReleaseImportResult
from .release_inspect import ReleaseInspection
from .release_verify import ReleaseVerificationResult


def record_from_verified_import(
    *,
    verification: ReleaseVerificationResult,
    inspection: ReleaseInspection,
    imported: ReleaseImportResult,
    metadata: Mapping[str, Any] | None = None,
) -> ScientificReleaseCatalogRecord:
    if not isinstance(verification, ReleaseVerificationResult):
        raise ValidationError(
            "verification must be ReleaseVerificationResult."
        )
    if not isinstance(inspection, ReleaseInspection):
        raise ValidationError(
            "inspection must be ReleaseInspection."
        )
    if not isinstance(imported, ReleaseImportResult):
        raise ValidationError(
            "imported must be ReleaseImportResult."
        )

    if not verification.valid:
        raise ValidationError(
            "unverified release cannot be registered as verified."
        )

    if (
        verification.release_id != inspection.release_id
        or verification.release_id != imported.release_id
    ):
        raise ValidationError(
            "release ID mismatch across verification/inspection/import."
        )

    if (
        verification.release_manifest_sha256
        != inspection.release_manifest_sha256
    ):
        raise ValidationError(
            "release manifest SHA-256 mismatch."
        )

    if verification.bundle_sha256 != imported.bundle_sha256:
        raise ValidationError(
            "bundle SHA-256 mismatch."
        )

    destination = Path(imported.destination_path)
    evidence_path = destination / "manifests" / "scientific_evidence.json"

    evidence: list[CatalogEvidenceRef] = []

    if evidence_path.is_file():
        payload = json.loads(
            evidence_path.read_text(encoding="utf-8")
        )
        for item in payload.get("evidence", []):
            evidence.append(
                CatalogEvidenceRef(
                    evidence_type=item["evidence_type"],
                    evidence_id=item["evidence_id"],
                    sha256=item["sha256"],
                    metadata=item.get("metadata", {}),
                )
            )

    component_kinds = tuple(
        sorted(
            {
                str(item.get("kind"))
                for item in inspection.components
                if item.get("kind")
            }
        )
    )

    return ScientificReleaseCatalogRecord(
        release_id=inspection.release_id,
        release_name=inspection.release_name,
        campaign_id=inspection.campaign_id,
        experiment_id=inspection.experiment_id,
        release_manifest_sha256=inspection.release_manifest_sha256,
        bundle_sha256=verification.bundle_sha256,
        import_path=str(destination),
        trust_status=CatalogTrustStatus.VERIFIED,
        component_kinds=component_kinds,
        evidence=tuple(evidence),
        metadata=dict(metadata or {}),
    )
