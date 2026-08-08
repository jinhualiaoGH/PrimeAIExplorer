from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from typing import Any

from kernel.exceptions import ValidationError
from experimental_campaign.identity import sha256_json


class PhaseIStage(str, Enum):
    I1 = "I1"
    I2 = "I2"
    I3 = "I3"
    I4 = "I4"
    I5 = "I5"
    I6 = "I6"
    I7 = "I7"
    I8 = "I8"


@dataclass(frozen=True, slots=True)
class PhaseIStageContract:
    stage: PhaseIStage
    title: str
    capability: str
    public_symbols: tuple[str, ...]
    depends_on: tuple[PhaseIStage, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.stage, PhaseIStage):
            try:
                object.__setattr__(self, "stage", PhaseIStage(self.stage))
            except Exception as exc:
                raise ValidationError("invalid Phase I stage.") from exc

        for name in ("title", "capability"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())

        symbols = tuple(sorted(set(self.public_symbols)))
        if not symbols or any(not isinstance(item, str) or not item.strip() for item in symbols):
            raise ValidationError("public_symbols must contain non-empty strings.")
        object.__setattr__(self, "public_symbols", symbols)

        deps = tuple(self.depends_on)
        if any(not isinstance(item, PhaseIStage) for item in deps):
            raise ValidationError("depends_on must contain PhaseIStage values.")
        object.__setattr__(self, "depends_on", deps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "title": self.title,
            "capability": self.capability,
            "public_symbols": list(self.public_symbols),
            "depends_on": [item.value for item in self.depends_on],
        }


@dataclass(frozen=True, slots=True)
class PhaseIArchitectureContract:
    architecture_id: str
    version: str
    stages: tuple[PhaseIStageContract, ...]

    def __post_init__(self) -> None:
        for name in ("architecture_id", "version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())

        stages = tuple(self.stages)
        if any(not isinstance(item, PhaseIStageContract) for item in stages):
            raise ValidationError("stages must contain PhaseIStageContract values.")

        stage_ids = [item.stage for item in stages]
        if len(stage_ids) != len(set(stage_ids)):
            raise ValidationError("duplicate Phase I stage contracts.")

        expected = tuple(PhaseIStage)
        if tuple(item.stage for item in stages) != expected:
            raise ValidationError(
                "Phase I architecture must contain ordered stages I1 through I8."
            )

        seen: set[PhaseIStage] = set()
        for item in stages:
            if any(dep not in seen for dep in item.depends_on):
                raise ValidationError(
                    f"{item.stage.value} depends on a stage not yet established."
                )
            seen.add(item.stage)

        object.__setattr__(self, "stages", stages)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "i8.0",
            "architecture_id": self.architecture_id,
            "version": self.version,
            "stages": [item.to_dict() for item in self.stages],
        }

    @property
    def architecture_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["architecture_sha256"] = self.architecture_sha256
        return payload


@dataclass(frozen=True, slots=True)
class PhaseISelfAudit:
    valid: bool
    checked_symbols: int
    missing_symbols: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "i8.0",
            "valid": self.valid,
            "checked_symbols": self.checked_symbols,
            "missing_symbols": list(self.missing_symbols),
        }


def build_phase_i_architecture_contract() -> PhaseIArchitectureContract:
    return PhaseIArchitectureContract(
        architecture_id="PrimeAIExplorer-Phase-I",
        version="4.0.0",
        stages=(
            PhaseIStageContract(
                PhaseIStage.I1,
                "Campaign Repository & Persistence Contracts",
                "Canonical logical repository identity and immutable repository records.",
                (
                    "CampaignRepository",
                    "CampaignRepositoryManifest",
                ),
            ),
            PhaseIStageContract(
                PhaseIStage.I2,
                "Durable Artifact Store & Content Addressing",
                "Content-addressed durable scientific artifacts and artifact manifests.",
                (
                    "DurableArtifactStore",
                    "ArtifactStoreManifest",
                ),
                (PhaseIStage.I1,),
            ),
            PhaseIStageContract(
                PhaseIStage.I3,
                "Campaign Checkpoint & Resume Engine",
                "Durable execution state, checkpoint lineage, and safe resume.",
                (
                    "CampaignCheckpoint",
                    "CampaignCheckpointStore",
                    "ResumePlanner",
                    "audit_checkpoint_lineage",
                ),
                (PhaseIStage.I1, PhaseIStage.I2),
            ),
            PhaseIStageContract(
                PhaseIStage.I4,
                "Reproducibility Verification Engine",
                "Campaign-level integrity verification and reproducibility certificates.",
                (
                    "CampaignReproducibilityVerifier",
                    "ReproducibilityCertificate",
                    "EvidenceIdentity",
                ),
                (PhaseIStage.I1, PhaseIStage.I2, PhaseIStage.I3),
            ),
            PhaseIStageContract(
                PhaseIStage.I5,
                "Scientific Release Bundle Builder",
                "Deterministic portable scientific release construction.",
                (
                    "ScientificReleaseBundleBuilder",
                    "ScientificReleaseManifest",
                    "ReleaseBuildResult",
                ),
                (PhaseIStage.I4,),
            ),
            PhaseIStageContract(
                PhaseIStage.I6,
                "Scientific Release Verification & Import Engine",
                "Independent release verification, safe import, and inspection.",
                (
                    "ScientificReleaseVerifier",
                    "ScientificReleaseImporter",
                    "inspect_release",
                ),
                (PhaseIStage.I5,),
            ),
            PhaseIStageContract(
                PhaseIStage.I7,
                "Scientific Release Catalog & Query Service",
                "Persistent trusted release catalog, indexing, search, and snapshot export.",
                (
                    "ScientificReleaseCatalog",
                    "ScientificReleaseCatalogQueryService",
                    "record_from_verified_import",
                    "export_catalog_snapshot",
                ),
                (PhaseIStage.I6,),
            ),
            PhaseIStageContract(
                PhaseIStage.I8,
                "Phase I Integration & Architecture Freeze",
                "End-to-end integration contract and frozen Phase I public architecture.",
                (
                    "PhaseIArchitectureContract",
                    "PhaseIReferenceWorkflow",
                    "build_phase_i_architecture_contract",
                    "phase_i_self_audit",
                ),
                (
                    PhaseIStage.I1,
                    PhaseIStage.I2,
                    PhaseIStage.I3,
                    PhaseIStage.I4,
                    PhaseIStage.I5,
                    PhaseIStage.I6,
                    PhaseIStage.I7,
                ),
            ),
        ),
    )


def phase_i_self_audit(
    module_name: str = "campaign_repository",
) -> PhaseISelfAudit:
    module = import_module(module_name)
    contract = build_phase_i_architecture_contract()

    missing: list[str] = []
    checked = 0

    for stage in contract.stages:
        for symbol in stage.public_symbols:
            checked += 1
            if not hasattr(module, symbol):
                missing.append(f"{stage.stage.value}:{symbol}")

    return PhaseISelfAudit(
        valid=(len(missing) == 0),
        checked_symbols=checked,
        missing_symbols=tuple(missing),
    )
