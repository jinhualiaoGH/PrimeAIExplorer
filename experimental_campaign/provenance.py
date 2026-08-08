from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .validation import require_text


@dataclass(frozen=True, slots=True)
class ProvenanceLink:
    relation: str
    subject_type: str
    subject_id: str
    subject_sha256: str
    object_type: str
    object_id: str
    object_sha256: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "relation",
            "subject_type",
            "subject_id",
            "subject_sha256",
            "object_type",
            "object_id",
            "object_sha256",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation": self.relation,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "subject_sha256": self.subject_sha256,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "object_sha256": self.object_sha256,
            "metadata": dict(self.metadata),
        }

    @property
    def link_sha256(self) -> str:
        return sha256_json(self.to_dict())


@dataclass(frozen=True, slots=True)
class ScientificProvenance:
    provenance_id: str
    experiment_id: str
    experiment_sha256: str
    materialization_sha256: str
    plan_id: str
    plan_sha256: str
    run_id: str
    run_sha256: str
    result_set_id: str
    result_set_sha256: str
    links: tuple[ProvenanceLink, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "provenance_id",
            "experiment_id",
            "experiment_sha256",
            "materialization_sha256",
            "plan_id",
            "plan_sha256",
            "run_id",
            "run_sha256",
            "result_set_id",
            "result_set_sha256",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        links = tuple(self.links)
        if any(not isinstance(item, ProvenanceLink) for item in links):
            raise ValidationError("links must contain ProvenanceLink values.")
        digests = tuple(item.link_sha256 for item in links)
        if len(set(digests)) != len(digests):
            raise ValidationError("links contains duplicate provenance links.")
        object.__setattr__(
            self,
            "links",
            tuple(sorted(links, key=lambda item: item.link_sha256)),
        )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h6.0",
            "experiment_id": self.experiment_id,
            "experiment_sha256": self.experiment_sha256,
            "materialization_sha256": self.materialization_sha256,
            "plan_id": self.plan_id,
            "plan_sha256": self.plan_sha256,
            "run_id": self.run_id,
            "run_sha256": self.run_sha256,
            "result_set_id": self.result_set_id,
            "result_set_sha256": self.result_set_sha256,
            "link_sha256s": [item.link_sha256 for item in self.links],
            "metadata": dict(self.metadata),
        }

    @property
    def provenance_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "provenance_id": self.provenance_id,
                "provenance_sha256": self.provenance_sha256,
                "links": [item.to_dict() for item in self.links],
            }
        )
        return payload
