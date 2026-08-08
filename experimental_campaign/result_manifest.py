from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .result_assembly import CampaignAssembly
from .validation import require_text


@dataclass(frozen=True, slots=True)
class CampaignResultManifest:
    assembly_sha256: str
    result_set_id: str
    result_set_sha256: str
    provenance_id: str
    provenance_sha256: str
    experiment_id: str
    experiment_sha256: str
    materialization_sha256: str
    plan_id: str
    plan_sha256: str
    run_id: str
    run_sha256: str
    result_count: int
    succeeded_count: int
    failed_count: int
    exhausted_count: int
    result_sha256s: tuple[str, ...]
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "assembly_sha256",
            "result_set_id",
            "result_set_sha256",
            "provenance_id",
            "provenance_sha256",
            "experiment_id",
            "experiment_sha256",
            "materialization_sha256",
            "plan_id",
            "plan_sha256",
            "run_id",
            "run_sha256",
            "source",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        for name in (
            "result_count",
            "succeeded_count",
            "failed_count",
            "exhausted_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValidationError(f"{name} must be a non-negative integer.")

        if self.succeeded_count + self.failed_count + self.exhausted_count != self.result_count:
            raise ValidationError("terminal result counts must equal result_count.")

        digests = tuple(require_text("result_sha256", value) for value in self.result_sha256s)
        if len(digests) != self.result_count:
            raise ValidationError("result_sha256s count must equal result_count.")
        if len(set(digests)) != len(digests):
            raise ValidationError("result_sha256s contains duplicate result identities.")
        object.__setattr__(self, "result_sha256s", tuple(sorted(digests)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @classmethod
    def from_assembly(
        cls,
        assembly: CampaignAssembly,
        *,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CampaignResultManifest":
        if not isinstance(assembly, CampaignAssembly):
            raise ValidationError("assembly must be CampaignAssembly.")

        result_set = assembly.result_set
        provenance = assembly.provenance

        return cls(
            assembly_sha256=assembly.assembly_sha256,
            result_set_id=result_set.result_set_id,
            result_set_sha256=result_set.result_set_sha256,
            provenance_id=provenance.provenance_id,
            provenance_sha256=provenance.provenance_sha256,
            experiment_id=result_set.experiment_id,
            experiment_sha256=result_set.experiment_sha256,
            materialization_sha256=result_set.materialization_sha256,
            plan_id=result_set.plan_id,
            plan_sha256=result_set.plan_sha256,
            run_id=result_set.run_id,
            run_sha256=result_set.run_sha256,
            result_count=result_set.result_count,
            succeeded_count=result_set.succeeded_count,
            failed_count=result_set.failed_count,
            exhausted_count=result_set.exhausted_count,
            result_sha256s=tuple(
                item.result_sha256 for item in result_set.results
            ),
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h6.0",
            "assembly_sha256": self.assembly_sha256,
            "result_set_id": self.result_set_id,
            "result_set_sha256": self.result_set_sha256,
            "provenance_id": self.provenance_id,
            "provenance_sha256": self.provenance_sha256,
            "experiment_id": self.experiment_id,
            "experiment_sha256": self.experiment_sha256,
            "materialization_sha256": self.materialization_sha256,
            "plan_id": self.plan_id,
            "plan_sha256": self.plan_sha256,
            "run_id": self.run_id,
            "run_sha256": self.run_sha256,
            "result_count": self.result_count,
            "succeeded_count": self.succeeded_count,
            "failed_count": self.failed_count,
            "exhausted_count": self.exhausted_count,
            "result_sha256s": list(self.result_sha256s),
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())
