from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from kernel.exceptions import ValidationError
from experimental_campaign.identity import canonical_metadata, sha256_json

from .artifact_store import ArtifactVerification, DurableArtifactStore
from .contracts import ArtifactDescriptor


@dataclass(frozen=True, slots=True)
class ArtifactStoreManifest:
    store_id: str
    artifacts: tuple[ArtifactDescriptor, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.store_id, str) or not self.store_id.strip():
            raise ValidationError("store_id must be a non-empty string.")
        object.__setattr__(self, "store_id", self.store_id.strip())

        artifacts = tuple(self.artifacts)
        if any(not isinstance(item, ArtifactDescriptor) for item in artifacts):
            raise ValidationError(
                "artifacts must contain ArtifactDescriptor values."
            )

        # Same bytes may appear under multiple logical names, but each
        # descriptor identity inside one manifest must remain unique.
        keys = [
            (item.name, item.sha256, item.relative_path)
            for item in artifacts
        ]
        if len(keys) != len(set(keys)):
            raise ValidationError("artifact manifest contains duplicate descriptors.")

        object.__setattr__(
            self,
            "artifacts",
            tuple(
                sorted(
                    artifacts,
                    key=lambda item: (
                        item.sha256,
                        item.name,
                        item.relative_path,
                    ),
                )
            ),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    @property
    def unique_blob_count(self) -> int:
        return len({item.sha256 for item in self.artifacts})

    @property
    def logical_size_bytes(self) -> int:
        return sum(item.size_bytes for item in self.artifacts)

    @property
    def unique_size_bytes(self) -> int:
        by_sha: dict[str, int] = {}
        for item in self.artifacts:
            by_sha.setdefault(item.sha256, item.size_bytes)
        return sum(by_sha.values())

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "i2.0",
            "store_id": self.store_id,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "manifest_sha256": self.manifest_sha256,
                "artifact_count": self.artifact_count,
                "unique_blob_count": self.unique_blob_count,
                "logical_size_bytes": self.logical_size_bytes,
                "unique_size_bytes": self.unique_size_bytes,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class ArtifactIntegrityAudit:
    manifest_sha256: str
    verifications: tuple[ArtifactVerification, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_sha256, str) or not self.manifest_sha256.strip():
            raise ValidationError("manifest_sha256 must be non-empty.")
        verifications = tuple(self.verifications)
        if any(not isinstance(item, ArtifactVerification) for item in verifications):
            raise ValidationError(
                "verifications must contain ArtifactVerification values."
            )
        object.__setattr__(self, "verifications", verifications)

    @property
    def checked_count(self) -> int:
        return len(self.verifications)

    @property
    def valid_count(self) -> int:
        return sum(item.valid for item in self.verifications)

    @property
    def invalid_count(self) -> int:
        return self.checked_count - self.valid_count

    @property
    def valid(self) -> bool:
        return self.invalid_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "i2.0",
            "manifest_sha256": self.manifest_sha256,
            "checked_count": self.checked_count,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "valid": self.valid,
            "verifications": [item.to_dict() for item in self.verifications],
        }


def audit_artifact_manifest(
    *,
    store: DurableArtifactStore,
    manifest: ArtifactStoreManifest,
) -> ArtifactIntegrityAudit:
    if not isinstance(store, DurableArtifactStore):
        raise ValidationError("store must be DurableArtifactStore.")
    if not isinstance(manifest, ArtifactStoreManifest):
        raise ValidationError("manifest must be ArtifactStoreManifest.")

    return ArtifactIntegrityAudit(
        manifest_sha256=manifest.manifest_sha256,
        verifications=store.verify_many(manifest.artifacts),
    )
