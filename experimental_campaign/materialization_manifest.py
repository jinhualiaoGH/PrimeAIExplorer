from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .materialization import ExperimentMaterialization
from .validation import require_text


@dataclass(frozen=True, slots=True)
class MaterializationManifest:
    experiment_id: str
    experiment_sha256: str
    input_suite_sha256: str
    materialization_sha256: str
    case_count: int
    case_ids: tuple[str, ...]
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "experiment_id",
            "experiment_sha256",
            "input_suite_sha256",
            "materialization_sha256",
            "source",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if (
            isinstance(self.case_count, bool)
            or not isinstance(self.case_count, int)
            or self.case_count < 0
        ):
            raise ValidationError("case_count must be a non-negative integer.")

        ids = tuple(require_text("case_id", value) for value in self.case_ids)
        if len(ids) != self.case_count:
            raise ValidationError("case_count does not match case_ids.")
        if len(set(ids)) != len(ids):
            raise ValidationError("case_ids contains duplicate IDs.")
        object.__setattr__(self, "case_ids", tuple(sorted(ids)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @classmethod
    def from_materialization(
        cls,
        materialization: ExperimentMaterialization,
        *,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "MaterializationManifest":
        if not isinstance(materialization, ExperimentMaterialization):
            raise ValidationError(
                "materialization must be ExperimentMaterialization."
            )

        return cls(
            experiment_id=materialization.experiment_id,
            experiment_sha256=materialization.experiment_sha256,
            input_suite_sha256=materialization.input_suite_sha256,
            materialization_sha256=materialization.materialization_sha256,
            case_count=materialization.case_count,
            case_ids=tuple(case.case_id for case in materialization.cases),
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h3.0",
            "experiment_id": self.experiment_id,
            "experiment_sha256": self.experiment_sha256,
            "input_suite_sha256": self.input_suite_sha256,
            "materialization_sha256": self.materialization_sha256,
            "case_count": self.case_count,
            "case_ids": list(self.case_ids),
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())
