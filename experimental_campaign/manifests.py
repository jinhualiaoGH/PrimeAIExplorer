from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .contracts import CampaignSpec, ExperimentDefinition
from .identity import canonical_metadata, sha256_json
from .validation import require_text


def _validate_sha256(name: str, value: str) -> str:
    value = require_text(name, value)
    if len(value) != 64:
        raise ValidationError(f"{name} must be 64 hex characters.")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValidationError(f"{name} must be hexadecimal.") from exc
    return value.lower()


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    experiment_id: str
    experiment_sha256: str
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "experiment_id", require_text("experiment_id", self.experiment_id))
        object.__setattr__(
            self,
            "experiment_sha256",
            _validate_sha256("experiment_sha256", self.experiment_sha256),
        )
        object.__setattr__(self, "source", require_text("source", self.source))
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @classmethod
    def from_experiment(
        cls,
        experiment: ExperimentDefinition,
        *,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ExperimentManifest":
        if not isinstance(experiment, ExperimentDefinition):
            raise ValidationError("experiment must be ExperimentDefinition.")
        return cls(
            experiment_id=experiment.experiment_id,
            experiment_sha256=experiment.experiment_sha256,
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h1.0",
            "experiment_id": self.experiment_id,
            "experiment_sha256": self.experiment_sha256,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())


@dataclass(frozen=True, slots=True)
class CampaignManifest:
    campaign_id: str
    campaign_sha256: str
    experiment_manifests: tuple[ExperimentManifest, ...]
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "campaign_id", require_text("campaign_id", self.campaign_id))
        object.__setattr__(
            self,
            "campaign_sha256",
            _validate_sha256("campaign_sha256", self.campaign_sha256),
        )
        manifests = tuple(self.experiment_manifests)
        for item in manifests:
            if not isinstance(item, ExperimentManifest):
                raise ValidationError(
                    "experiment_manifests must contain ExperimentManifest values."
                )
        experiment_ids = tuple(item.experiment_id for item in manifests)
        if len(set(experiment_ids)) != len(experiment_ids):
            raise ValidationError(
                "experiment_manifests contains duplicate experiment IDs."
            )
        object.__setattr__(
            self,
            "experiment_manifests",
            tuple(sorted(manifests, key=lambda item: item.experiment_id)),
        )
        object.__setattr__(self, "source", require_text("source", self.source))
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @classmethod
    def from_campaign(
        cls,
        campaign: CampaignSpec,
        *,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CampaignManifest":
        if not isinstance(campaign, CampaignSpec):
            raise ValidationError("campaign must be CampaignSpec.")
        manifests = tuple(
            ExperimentManifest.from_experiment(experiment, source=source)
            for experiment in campaign.experiments
        )
        return cls(
            campaign_id=campaign.campaign_id,
            campaign_sha256=campaign.campaign_sha256,
            experiment_manifests=manifests,
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h1.0",
            "campaign_id": self.campaign_id,
            "campaign_sha256": self.campaign_sha256,
            "experiment_manifests": [item.to_dict() for item in self.experiment_manifests],
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())
