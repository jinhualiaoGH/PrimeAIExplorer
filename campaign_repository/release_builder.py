from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from kernel.exceptions import ValidationError
from experimental_campaign.identity import sha256_json

from .artifact_manifest import ArtifactStoreManifest
from .checkpoint_contracts import CampaignCheckpoint
from .contracts import CampaignRepositoryManifest
from .reproducibility_contracts import (
    EvidenceIdentity,
    ReproducibilityCertificate,
)
from .release_contracts import (
    ReleaseBuildResult,
    ReleaseComponent,
    ReleaseComponentKind,
    ScientificReleaseManifest,
)
from .release_io import (
    deterministic_zip_bytes,
    sha256_bytes,
    write_immutable_bundle,
)


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _safe_release_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            "release_name must be a non-empty string."
        )
    value = value.strip()
    if value in {".", ".."}:
        raise ValidationError("invalid release_name.")
    if any(char in value for char in ("/", "\\", "\0")):
        raise ValidationError(
            "release_name contains forbidden characters."
        )
    return value


class ScientificReleaseBundleBuilder:
    def build(
        self,
        *,
        output_dir: str | Path,
        release_name: str,
        campaign_id: str,
        experiment_id: str,
        repository_manifest: CampaignRepositoryManifest | None = None,
        artifact_manifest: ArtifactStoreManifest | None = None,
        checkpoints: Iterable[CampaignCheckpoint] = (),
        reproducibility_certificate: ReproducibilityCertificate | None = None,
        scientific_evidence: Iterable[EvidenceIdentity] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> ReleaseBuildResult:
        output_dir = Path(output_dir)
        release_name = _safe_release_name(release_name)

        component_payloads: dict[str, bytes] = {}
        components: list[ReleaseComponent] = []

        if repository_manifest is not None:
            if not isinstance(
                repository_manifest,
                CampaignRepositoryManifest,
            ):
                raise ValidationError(
                    "repository_manifest must be CampaignRepositoryManifest."
                )
            self._add_json_component(
                components=components,
                payloads=component_payloads,
                component_id="repository-manifest",
                kind=ReleaseComponentKind.REPOSITORY_MANIFEST,
                relative_path="manifests/repository.json",
                payload=repository_manifest.to_dict(),
                metadata={
                    "repository_id": repository_manifest.repository_id,
                    "entry_count": repository_manifest.entry_count,
                },
            )

        if artifact_manifest is not None:
            if not isinstance(
                artifact_manifest,
                ArtifactStoreManifest,
            ):
                raise ValidationError(
                    "artifact_manifest must be ArtifactStoreManifest."
                )
            self._add_json_component(
                components=components,
                payloads=component_payloads,
                component_id="artifact-manifest",
                kind=ReleaseComponentKind.ARTIFACT_MANIFEST,
                relative_path="manifests/artifacts.json",
                payload=artifact_manifest.to_dict(),
                metadata={
                    "store_id": artifact_manifest.store_id,
                    "artifact_count": artifact_manifest.artifact_count,
                    "unique_blob_count": artifact_manifest.unique_blob_count,
                },
            )

        checkpoints = tuple(checkpoints)
        if checkpoints:
            if any(
                not isinstance(item, CampaignCheckpoint)
                for item in checkpoints
            ):
                raise ValidationError(
                    "checkpoints must contain CampaignCheckpoint values."
                )
            ordered = tuple(
                sorted(
                    checkpoints,
                    key=lambda item: item.checkpoint_sequence,
                )
            )
            self._add_json_component(
                components=components,
                payloads=component_payloads,
                component_id="checkpoint-lineage",
                kind=ReleaseComponentKind.CHECKPOINT_LINEAGE,
                relative_path="manifests/checkpoints.json",
                payload={
                    "schema_version": "i5.0",
                    "checkpoints": [
                        item.to_dict()
                        for item in ordered
                    ],
                },
                metadata={
                    "checkpoint_count": len(ordered),
                    "first_sequence": ordered[0].checkpoint_sequence,
                    "last_sequence": ordered[-1].checkpoint_sequence,
                },
            )

        if reproducibility_certificate is not None:
            if not isinstance(
                reproducibility_certificate,
                ReproducibilityCertificate,
            ):
                raise ValidationError(
                    "reproducibility_certificate must be ReproducibilityCertificate."
                )
            self._add_json_component(
                components=components,
                payloads=component_payloads,
                component_id="reproducibility-certificate",
                kind=ReleaseComponentKind.REPRODUCIBILITY_CERTIFICATE,
                relative_path="manifests/reproducibility_certificate.json",
                payload=reproducibility_certificate.to_dict(),
                metadata={
                    "certificate_id": reproducibility_certificate.certificate_id,
                    "certificate_sha256": reproducibility_certificate.certificate_sha256,
                    "reproducible": reproducibility_certificate.reproducible,
                },
            )

        scientific_evidence = tuple(scientific_evidence)
        if scientific_evidence:
            if any(
                not isinstance(item, EvidenceIdentity)
                for item in scientific_evidence
            ):
                raise ValidationError(
                    "scientific_evidence must contain EvidenceIdentity values."
                )
            ordered = tuple(
                sorted(
                    scientific_evidence,
                    key=lambda item: (
                        item.evidence_type,
                        item.evidence_id,
                        item.sha256,
                    ),
                )
            )
            self._add_json_component(
                components=components,
                payloads=component_payloads,
                component_id="scientific-evidence",
                kind=ReleaseComponentKind.SCIENTIFIC_EVIDENCE,
                relative_path="manifests/scientific_evidence.json",
                payload={
                    "schema_version": "i5.0",
                    "evidence": [
                        item.to_dict()
                        for item in ordered
                    ],
                },
                metadata={
                    "evidence_count": len(ordered),
                },
            )

        metadata_payload = dict(metadata or {})
        if metadata_payload:
            self._add_json_component(
                components=components,
                payloads=component_payloads,
                component_id="release-metadata",
                kind=ReleaseComponentKind.RELEASE_METADATA,
                relative_path="release/metadata.json",
                payload={
                    "schema_version": "i5.0",
                    "metadata": metadata_payload,
                },
                metadata={
                    "field_count": len(metadata_payload),
                },
            )

        manifest_seed = {
            "schema_version": "i5.0",
            "release_name": release_name,
            "campaign_id": campaign_id,
            "experiment_id": experiment_id,
            "components": [
                item.to_dict()
                for item in sorted(
                    components,
                    key=lambda item: (
                        item.kind.value,
                        item.component_id,
                        item.relative_path,
                    ),
                )
            ],
            "metadata": metadata_payload,
        }

        release_id = (
            "RELEASE-"
            + sha256_json(manifest_seed)[:20].upper()
        )

        manifest = ScientificReleaseManifest(
            release_id=release_id,
            release_name=release_name,
            campaign_id=campaign_id,
            experiment_id=experiment_id,
            components=tuple(components),
            metadata=metadata_payload,
        )

        manifest_bytes = _canonical_json_bytes(
            manifest.to_dict()
        )

        checksums_lines = [
            f"{item.sha256}  {item.relative_path}"
            for item in manifest.components
        ]
        checksums_lines.append(
            f"{sha256_bytes(manifest_bytes)}  release/manifest.json"
        )
        checksums_bytes = (
            "\n".join(sorted(checksums_lines)) + "\n"
        ).encode("utf-8")

        index_payload = {
            "schema_version": "i5.0",
            "release_id": manifest.release_id,
            "release_name": manifest.release_name,
            "campaign_id": manifest.campaign_id,
            "experiment_id": manifest.experiment_id,
            "release_manifest_sha256": manifest.release_manifest_sha256,
            "component_count": manifest.component_count,
            "manifest_path": "release/manifest.json",
            "checksums_path": "release/checksums.sha256",
            "components": [
                {
                    "component_id": item.component_id,
                    "kind": item.kind.value,
                    "relative_path": item.relative_path,
                    "sha256": item.sha256,
                }
                for item in manifest.components
            ],
        }
        index_bytes = _canonical_json_bytes(index_payload)

        entries = dict(component_payloads)
        entries["release/manifest.json"] = manifest_bytes
        entries["release/index.json"] = index_bytes
        entries["release/checksums.sha256"] = checksums_bytes

        bundle_bytes = deterministic_zip_bytes(entries)
        bundle_sha256 = sha256_bytes(bundle_bytes)

        filename = (
            f"{release_name}-"
            f"{manifest.release_manifest_sha256[:12]}.zip"
        )
        bundle_path = output_dir / filename

        write_immutable_bundle(
            bundle_path,
            bundle_bytes,
        )

        return ReleaseBuildResult(
            manifest=manifest,
            bundle_path=str(bundle_path),
            bundle_sha256=bundle_sha256,
            bundle_size_bytes=len(bundle_bytes),
            entry_count=len(entries),
        )

    @staticmethod
    def _add_json_component(
        *,
        components: list[ReleaseComponent],
        payloads: dict[str, bytes],
        component_id: str,
        kind: ReleaseComponentKind,
        relative_path: str,
        payload: Any,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        data = _canonical_json_bytes(payload)
        digest = sha256_bytes(data)

        component = ReleaseComponent(
            component_id=component_id,
            kind=kind,
            sha256=digest,
            relative_path=relative_path,
            metadata=dict(metadata or {}),
        )

        if relative_path in payloads:
            raise ValidationError(
                f"duplicate release component path: {relative_path}"
            )

        payloads[relative_path] = data
        components.append(component)
