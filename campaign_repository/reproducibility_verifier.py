from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any

from kernel.exceptions import ValidationError
from experimental_campaign.identity import sha256_json

from .artifact_manifest import (
    ArtifactStoreManifest,
    audit_artifact_manifest,
)
from .artifact_store import DurableArtifactStore
from .checkpoint_audit import audit_checkpoint_lineage
from .checkpoint_contracts import CampaignCheckpoint
from .contracts import CampaignRepositoryManifest
from .repository import CampaignRepository
from .reproducibility_contracts import (
    EvidenceIdentity,
    ReproducibilityCertificate,
    VerificationCheck,
    VerificationStatus,
)


def _evidence(
    evidence_type: str,
    evidence_id: str,
    sha256: str,
    **metadata: Any,
) -> EvidenceIdentity:
    return EvidenceIdentity(
        evidence_type=evidence_type,
        evidence_id=evidence_id,
        sha256=sha256,
        metadata=metadata,
    )


@dataclass(frozen=True, slots=True)
class CampaignReproducibilityVerifier:
    def verify(
        self,
        *,
        campaign_id: str,
        experiment_id: str,
        repository: CampaignRepository | None = None,
        repository_manifest: CampaignRepositoryManifest | None = None,
        artifact_store: DurableArtifactStore | None = None,
        artifact_manifest: ArtifactStoreManifest | None = None,
        checkpoints: Iterable[CampaignCheckpoint] = (),
        scientific_evidence: Iterable[EvidenceIdentity] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> ReproducibilityCertificate:
        checks: list[VerificationCheck] = []

        checks.append(
            self._verify_repository(
                repository=repository,
                manifest=repository_manifest,
            )
        )
        checks.append(
            self._verify_artifacts(
                store=artifact_store,
                manifest=artifact_manifest,
            )
        )
        checkpoints = tuple(checkpoints)
        checks.append(
            self._verify_checkpoints(checkpoints)
        )
        checks.append(
            self._verify_scientific_evidence(
                scientific_evidence=tuple(scientific_evidence),
            )
        )

        seed = {
            "schema_version": "i4.0",
            "campaign_id": campaign_id,
            "experiment_id": experiment_id,
            "checks": [item.to_dict() for item in checks],
        }

        return ReproducibilityCertificate(
            certificate_id=f"REPRO-{sha256_json(seed)[:20].upper()}",
            campaign_id=campaign_id,
            experiment_id=experiment_id,
            checks=tuple(checks),
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _verify_repository(
        *,
        repository: CampaignRepository | None,
        manifest: CampaignRepositoryManifest | None,
    ) -> VerificationCheck:
        if repository is None and manifest is None:
            return VerificationCheck(
                check_id="repository",
                status=VerificationStatus.SKIPPED,
                message="repository verification not supplied",
            )
        if repository is None or manifest is None:
            return VerificationCheck(
                check_id="repository",
                status=VerificationStatus.FAILED,
                message="repository and repository_manifest must be supplied together",
            )

        try:
            repository.verify_manifest(manifest)
        except Exception as exc:
            return VerificationCheck(
                check_id="repository",
                status=VerificationStatus.FAILED,
                message=f"repository verification failed: {exc}",
                evidence=(
                    _evidence(
                        "repository_manifest",
                        manifest.repository_id,
                        manifest.manifest_sha256,
                    ),
                ),
            )

        return VerificationCheck(
            check_id="repository",
            status=VerificationStatus.PASSED,
            message="repository manifest and entries verified",
            evidence=(
                _evidence(
                    "repository_manifest",
                    manifest.repository_id,
                    manifest.manifest_sha256,
                    entry_count=manifest.entry_count,
                ),
            ),
        )

    @staticmethod
    def _verify_artifacts(
        *,
        store: DurableArtifactStore | None,
        manifest: ArtifactStoreManifest | None,
    ) -> VerificationCheck:
        if store is None and manifest is None:
            return VerificationCheck(
                check_id="artifacts",
                status=VerificationStatus.SKIPPED,
                message="artifact verification not supplied",
            )
        if store is None or manifest is None:
            return VerificationCheck(
                check_id="artifacts",
                status=VerificationStatus.FAILED,
                message="artifact_store and artifact_manifest must be supplied together",
            )

        try:
            audit = audit_artifact_manifest(
                store=store,
                manifest=manifest,
            )
        except Exception as exc:
            return VerificationCheck(
                check_id="artifacts",
                status=VerificationStatus.FAILED,
                message=f"artifact audit failed: {exc}",
                evidence=(
                    _evidence(
                        "artifact_manifest",
                        manifest.store_id,
                        manifest.manifest_sha256,
                    ),
                ),
            )

        status = (
            VerificationStatus.PASSED
            if audit.valid
            else VerificationStatus.FAILED
        )
        return VerificationCheck(
            check_id="artifacts",
            status=status,
            message=(
                "artifact manifest verified"
                if audit.valid
                else f"artifact integrity failures: {audit.invalid_count}"
            ),
            evidence=(
                _evidence(
                    "artifact_manifest",
                    manifest.store_id,
                    manifest.manifest_sha256,
                    artifact_count=manifest.artifact_count,
                    unique_blob_count=manifest.unique_blob_count,
                ),
            ),
            metadata={
                "checked_count": audit.checked_count,
                "valid_count": audit.valid_count,
                "invalid_count": audit.invalid_count,
            },
        )

    @staticmethod
    def _verify_checkpoints(
        checkpoints: tuple[CampaignCheckpoint, ...],
    ) -> VerificationCheck:
        if not checkpoints:
            return VerificationCheck(
                check_id="checkpoints",
                status=VerificationStatus.SKIPPED,
                message="checkpoint lineage not supplied",
            )

        audit = audit_checkpoint_lineage(checkpoints)
        ordered = tuple(
            sorted(
                checkpoints,
                key=lambda item: item.checkpoint_sequence,
            )
        )
        evidence = tuple(
            _evidence(
                "checkpoint",
                item.checkpoint_id,
                item.checkpoint_sha256,
                sequence=item.checkpoint_sequence,
                status=item.status.value,
            )
            for item in ordered
        )

        return VerificationCheck(
            check_id="checkpoints",
            status=(
                VerificationStatus.PASSED
                if audit.valid
                else VerificationStatus.FAILED
            ),
            message=(
                "checkpoint lineage verified"
                if audit.valid
                else "checkpoint lineage verification failed"
            ),
            evidence=evidence,
            metadata={
                "checked_count": audit.checked_count,
                "errors": list(audit.errors),
            },
        )

    @staticmethod
    def _verify_scientific_evidence(
        *,
        scientific_evidence: tuple[EvidenceIdentity, ...],
    ) -> VerificationCheck:
        if not scientific_evidence:
            return VerificationCheck(
                check_id="scientific_evidence",
                status=VerificationStatus.SKIPPED,
                message="scientific evidence identities not supplied",
            )

        keys = [
            (item.evidence_type, item.evidence_id)
            for item in scientific_evidence
        ]
        if len(keys) != len(set(keys)):
            return VerificationCheck(
                check_id="scientific_evidence",
                status=VerificationStatus.FAILED,
                message="duplicate scientific evidence identities",
                evidence=scientific_evidence,
            )

        return VerificationCheck(
            check_id="scientific_evidence",
            status=VerificationStatus.PASSED,
            message="scientific evidence identities recorded",
            evidence=scientific_evidence,
        )
