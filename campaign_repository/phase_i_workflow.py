from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .artifact_manifest import ArtifactStoreManifest
from .artifact_store import DurableArtifactStore
from .catalog_export import export_catalog_snapshot
from .catalog_query import CatalogQuery, ScientificReleaseCatalogQueryService
from .catalog_registration import record_from_verified_import
from .catalog_store import ScientificReleaseCatalog
from .checkpoint_contracts import CampaignCheckpoint
from .contracts import CampaignRepositoryManifest
from .release_builder import ScientificReleaseBundleBuilder
from .release_import import ScientificReleaseImporter
from .release_inspect import inspect_release
from .release_verify import ScientificReleaseVerifier
from .reproducibility_contracts import (
    EvidenceIdentity,
    ReproducibilityCertificate,
)
from .reproducibility_verifier import CampaignReproducibilityVerifier
from .repository import CampaignRepository


@dataclass(frozen=True, slots=True)
class PhaseIReferenceWorkflowResult:
    release_id: str
    release_manifest_sha256: str
    bundle_sha256: str
    reproducibility_certificate_sha256: str
    catalog_record_sha256: str
    catalog_sha256: str
    catalog_snapshot_sha256: str
    imported_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "i8.0",
            "release_id": self.release_id,
            "release_manifest_sha256": self.release_manifest_sha256,
            "bundle_sha256": self.bundle_sha256,
            "reproducibility_certificate_sha256": self.reproducibility_certificate_sha256,
            "catalog_record_sha256": self.catalog_record_sha256,
            "catalog_sha256": self.catalog_sha256,
            "catalog_snapshot_sha256": self.catalog_snapshot_sha256,
            "imported_path": self.imported_path,
        }


class PhaseIReferenceWorkflow:
    def run(
        self,
        *,
        root: str | Path,
        release_name: str,
        campaign_id: str,
        experiment_id: str,
        repository: CampaignRepository | None = None,
        repository_manifest: CampaignRepositoryManifest | None = None,
        artifact_store: DurableArtifactStore | None = None,
        artifact_manifest: ArtifactStoreManifest | None = None,
        checkpoints: tuple[CampaignCheckpoint, ...] = (),
        scientific_evidence: tuple[EvidenceIdentity, ...] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> PhaseIReferenceWorkflowResult:
        root = Path(root)

        certificate = CampaignReproducibilityVerifier().verify(
            campaign_id=campaign_id,
            experiment_id=experiment_id,
            repository=repository,
            repository_manifest=repository_manifest,
            artifact_store=artifact_store,
            artifact_manifest=artifact_manifest,
            checkpoints=checkpoints,
            scientific_evidence=scientific_evidence,
            metadata={"phase": "I8", **dict(metadata or {})},
        )

        if not certificate.reproducible:
            raise ValidationError(
                "Phase I reference workflow refuses to release non-reproducible evidence."
            )

        release = ScientificReleaseBundleBuilder().build(
            output_dir=root / "producer",
            release_name=release_name,
            campaign_id=campaign_id,
            experiment_id=experiment_id,
            repository_manifest=repository_manifest,
            artifact_manifest=artifact_manifest,
            checkpoints=checkpoints,
            reproducibility_certificate=certificate,
            scientific_evidence=scientific_evidence,
            metadata={"phase": "I8", **dict(metadata or {})},
        )

        verification = ScientificReleaseVerifier().verify(
            release.bundle_path,
            expected_bundle_sha256=release.bundle_sha256,
        )
        if not verification.valid:
            raise ValidationError(
                "I8 reference release failed I6 verification."
            )

        inspection = inspect_release(release.bundle_path)

        imported = ScientificReleaseImporter(
            root / "consumer"
        ).import_bundle(
            release.bundle_path,
            expected_bundle_sha256=release.bundle_sha256,
        )

        record = record_from_verified_import(
            verification=verification,
            inspection=inspection,
            imported=imported,
            metadata={"phase": "I8", **dict(metadata or {})},
        )

        catalog = ScientificReleaseCatalog(
            root / "catalog"
        )
        catalog.register(record)

        query = ScientificReleaseCatalogQueryService(catalog)
        found = query.search(
            CatalogQuery(
                release_id=record.release_id,
                verified_only=True,
            )
        )
        if len(found) != 1:
            raise ValidationError(
                "I8 catalog round-trip lookup failed."
            )

        snapshot = export_catalog_snapshot(
            catalog,
            root / "catalog_snapshot.json",
        )

        return PhaseIReferenceWorkflowResult(
            release_id=release.manifest.release_id,
            release_manifest_sha256=release.manifest.release_manifest_sha256,
            bundle_sha256=release.bundle_sha256,
            reproducibility_certificate_sha256=certificate.certificate_sha256,
            catalog_record_sha256=record.record_sha256,
            catalog_sha256=snapshot["catalog_sha256"],
            catalog_snapshot_sha256=snapshot["snapshot_sha256"],
            imported_path=imported.destination_path,
        )
