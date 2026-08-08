from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import zipfile
from typing import Any

from kernel.exceptions import ValidationError

from .release_verify import ScientificReleaseVerifier


@dataclass(frozen=True, slots=True)
class ReleaseInspection:
    release_id: str
    release_name: str
    campaign_id: str
    experiment_id: str
    release_manifest_sha256: str
    component_count: int
    components: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "i6.0",
            "release_id": self.release_id,
            "release_name": self.release_name,
            "campaign_id": self.campaign_id,
            "experiment_id": self.experiment_id,
            "release_manifest_sha256": self.release_manifest_sha256,
            "component_count": self.component_count,
            "components": list(self.components),
        }


def inspect_release(
    bundle_path: str | Path,
) -> ReleaseInspection:
    verifier = ScientificReleaseVerifier()
    result = verifier.verify(bundle_path)

    if not result.valid:
        raise ValidationError(
            "cannot inspect invalid release: "
            + "; ".join(result.errors)
        )

    with zipfile.ZipFile(bundle_path, "r") as archive:
        manifest = json.loads(
            archive.read(
                "release/manifest.json"
            ).decode("utf-8")
        )

    components = tuple(
        sorted(
            manifest.get("components", []),
            key=lambda item: (
                item.get("kind", ""),
                item.get("component_id", ""),
                item.get("relative_path", ""),
            ),
        )
    )

    return ReleaseInspection(
        release_id=manifest["release_id"],
        release_name=manifest["release_name"],
        campaign_id=manifest["campaign_id"],
        experiment_id=manifest["experiment_id"],
        release_manifest_sha256=manifest[
            "release_manifest_sha256"
        ],
        component_count=len(components),
        components=components,
    )
