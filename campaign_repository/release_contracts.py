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


def _require_sha256(value: str) -> str:
    value = _require_text("sha256", value).lower()
    if len(value) != 64 or any(
        char not in "0123456789abcdef"
        for char in value
    ):
        raise ValidationError(
            "sha256 must be a 64-character hexadecimal digest."
        )
    return value


class ReleaseComponentKind(str, Enum):
    REPOSITORY_MANIFEST = "repository_manifest"
    ARTIFACT_MANIFEST = "artifact_manifest"
    CHECKPOINT_LINEAGE = "checkpoint_lineage"
    REPRODUCIBILITY_CERTIFICATE = "reproducibility_certificate"
    SCIENTIFIC_EVIDENCE = "scientific_evidence"
    RELEASE_METADATA = "release_metadata"


@dataclass(frozen=True, slots=True)
class ReleaseComponent:
    component_id: str
    kind: ReleaseComponentKind
    sha256: str
    relative_path: str
    media_type: str = "application/json"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "component_id",
            _require_text("component_id", self.component_id),
        )
        if not isinstance(self.kind, ReleaseComponentKind):
            try:
                object.__setattr__(
                    self,
                    "kind",
                    ReleaseComponentKind(self.kind),
                )
            except Exception as exc:
                raise ValidationError(
                    "invalid release component kind."
                ) from exc

        object.__setattr__(
            self,
            "sha256",
            _require_sha256(self.sha256),
        )
        object.__setattr__(
            self,
            "relative_path",
            _require_text("relative_path", self.relative_path),
        )
        object.__setattr__(
            self,
            "media_type",
            _require_text("media_type", self.media_type),
        )

        if self.relative_path.startswith(("/", "\\")):
            raise ValidationError(
                "relative_path must be relative."
            )
        if ".." in self.relative_path.replace("\\", "/").split("/"):
            raise ValidationError(
                "relative_path cannot contain '..'."
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
            "component_id": self.component_id,
            "kind": self.kind.value,
            "sha256": self.sha256,
            "relative_path": self.relative_path.replace("\\", "/"),
            "media_type": self.media_type,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ScientificReleaseManifest:
    release_id: str
    release_name: str
    campaign_id: str
    experiment_id: str
    components: tuple[ReleaseComponent, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "release_id",
            "release_name",
            "campaign_id",
            "experiment_id",
        ):
            object.__setattr__(
                self,
                name,
                _require_text(name, getattr(self, name)),
            )

        components = tuple(self.components)
        if any(
            not isinstance(item, ReleaseComponent)
            for item in components
        ):
            raise ValidationError(
                "components must contain ReleaseComponent values."
            )

        ids = [item.component_id for item in components]
        paths = [item.relative_path for item in components]

        if len(ids) != len(set(ids)):
            raise ValidationError(
                "release manifest contains duplicate component IDs."
            )
        if len(paths) != len(set(paths)):
            raise ValidationError(
                "release manifest contains duplicate component paths."
            )

        object.__setattr__(
            self,
            "components",
            tuple(
                sorted(
                    components,
                    key=lambda item: (
                        item.kind.value,
                        item.component_id,
                        item.relative_path,
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
    def component_count(self) -> int:
        return len(self.components)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "i5.0",
            "release_name": self.release_name,
            "campaign_id": self.campaign_id,
            "experiment_id": self.experiment_id,
            "components": [
                item.to_dict()
                for item in self.components
            ],
            "metadata": dict(self.metadata),
        }

    @property
    def release_manifest_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "release_id": self.release_id,
                "release_manifest_sha256": self.release_manifest_sha256,
                "component_count": self.component_count,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class ReleaseBuildResult:
    manifest: ScientificReleaseManifest
    bundle_path: str
    bundle_sha256: str
    bundle_size_bytes: int
    entry_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, ScientificReleaseManifest):
            raise ValidationError(
                "manifest must be ScientificReleaseManifest."
            )
        object.__setattr__(
            self,
            "bundle_path",
            _require_text("bundle_path", self.bundle_path),
        )
        object.__setattr__(
            self,
            "bundle_sha256",
            _require_sha256(self.bundle_sha256),
        )

        for name in ("bundle_size_bytes", "entry_count"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
            ):
                raise ValidationError(
                    f"{name} must be a non-negative integer."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict(),
            "bundle_path": self.bundle_path,
            "bundle_sha256": self.bundle_sha256,
            "bundle_size_bytes": self.bundle_size_bytes,
            "entry_count": self.entry_count,
        }
