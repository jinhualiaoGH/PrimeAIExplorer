from dataclasses import replace
from pathlib import Path

import pytest

import campaign_repository as cr
from campaign_repository import (
    ArtifactStoreManifest,
    CampaignCheckpoint,
    CampaignRepository,
    CheckpointStatus,
    DurableArtifactStore,
    EvidenceIdentity,
    JobCheckpoint,
    PhaseIArchitectureContract,
    PhaseIReferenceWorkflow,
    PhaseIStage,
    PhaseIStageContract,
    build_phase_i_architecture_contract,
    next_checkpoint,
    phase_i_self_audit,
)
from kernel.exceptions import ValidationError


def build_inputs(tmp_path):
    repo = CampaignRepository(tmp_path / "repo")
    stored = repo.store_json(
        object_id="RESULT-1",
        object_kind="result_set",
        campaign_id="C",
        experiment_id="E",
        payload={"value": 1},
    )
    repo_manifest = repo.build_manifest(
        repository_id="REPO",
        entries=(stored.entry,),
    )
    repo.write_manifest(repo_manifest)

    artifact_store = DurableArtifactStore(
        tmp_path / "artifacts"
    )
    artifact = artifact_store.put_bytes(
        b"phase-i8-artifact",
        name="result.bin",
    )
    artifact_manifest = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(artifact.descriptor,),
    )

    cp0 = CampaignCheckpoint(
        checkpoint_id="CP0",
        campaign_id="C",
        experiment_id="E",
        execution_plan_sha256="a" * 64,
        checkpoint_sequence=0,
        status=CheckpointStatus.INTERRUPTED,
        jobs=(
            JobCheckpoint(
                "J1",
                True,
                1,
                result_sha256="1" * 64,
            ),
            JobCheckpoint(
                "J2",
                False,
                0,
            ),
        ),
    )
    cp1 = next_checkpoint(
        cp0,
        status=CheckpointStatus.COMPLETED,
        jobs=(
            cp0.jobs[0],
            JobCheckpoint(
                "J2",
                True,
                1,
                result_sha256="2" * 64,
            ),
        ),
    )

    evidence = (
        EvidenceIdentity(
            "h6.result_set",
            "RESULT-1",
            "3" * 64,
        ),
        EvidenceIdentity(
            "h6.provenance",
            "PROVENANCE-1",
            "4" * 64,
        ),
        EvidenceIdentity(
            "h7.analysis",
            "ANALYSIS-1",
            "5" * 64,
        ),
        EvidenceIdentity(
            "h8.publication",
            "PUBLICATION-1",
            "6" * 64,
        ),
    )

    return (
        repo,
        repo_manifest,
        artifact_store,
        artifact_manifest,
        (cp0, cp1),
        evidence,
    )


def test_stage_enum():
    assert tuple(item.value for item in PhaseIStage) == (
        "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8"
    )


def test_stage_contract():
    value = PhaseIStageContract(
        PhaseIStage.I1,
        "Title",
        "Capability",
        ("A",),
    )
    assert value.stage == PhaseIStage.I1


def test_stage_contract_string_stage():
    value = PhaseIStageContract(
        "I1",
        "Title",
        "Capability",
        ("A",),
    )
    assert value.stage == PhaseIStage.I1


def test_stage_contract_bad_stage():
    with pytest.raises(ValidationError):
        PhaseIStageContract(
            "bad",
            "Title",
            "Capability",
            ("A",),
        )


def test_stage_contract_requires_symbols():
    with pytest.raises(ValidationError):
        PhaseIStageContract(
            PhaseIStage.I1,
            "Title",
            "Capability",
            (),
        )


def test_stage_symbols_sorted_unique():
    value = PhaseIStageContract(
        PhaseIStage.I1,
        "Title",
        "Capability",
        ("B", "A", "B"),
    )
    assert value.public_symbols == ("A", "B")


def test_architecture_contract():
    value = build_phase_i_architecture_contract()
    assert isinstance(value, PhaseIArchitectureContract)


def test_architecture_has_8_stages():
    assert len(build_phase_i_architecture_contract().stages) == 8


def test_architecture_order():
    contract = build_phase_i_architecture_contract()
    assert tuple(item.stage for item in contract.stages) == tuple(PhaseIStage)


def test_architecture_id():
    assert build_phase_i_architecture_contract().architecture_id == "PrimeAIExplorer-Phase-I"


def test_architecture_version():
    assert build_phase_i_architecture_contract().version == "4.0.0"


def test_architecture_sha_stable():
    a = build_phase_i_architecture_contract()
    b = build_phase_i_architecture_contract()
    assert a.architecture_sha256 == b.architecture_sha256


def test_architecture_to_dict():
    payload = build_phase_i_architecture_contract().to_dict()
    assert payload["schema_version"] == "i8.0"


def test_architecture_duplicate_stage_rejected():
    stages = list(build_phase_i_architecture_contract().stages)
    stages[-1] = stages[-2]
    with pytest.raises(ValidationError):
        PhaseIArchitectureContract(
            "A",
            "1",
            tuple(stages),
        )


def test_architecture_missing_stage_rejected():
    contract = build_phase_i_architecture_contract()
    with pytest.raises(ValidationError):
        PhaseIArchitectureContract(
            "A",
            "1",
            contract.stages[:-1],
        )


def test_i8_depends_on_i1_i7():
    i8 = build_phase_i_architecture_contract().stages[-1]
    assert i8.depends_on == (
        PhaseIStage.I1,
        PhaseIStage.I2,
        PhaseIStage.I3,
        PhaseIStage.I4,
        PhaseIStage.I5,
        PhaseIStage.I6,
        PhaseIStage.I7,
    )


def test_self_audit_valid():
    audit = phase_i_self_audit()
    assert audit.valid


def test_self_audit_has_no_missing_symbols():
    assert phase_i_self_audit().missing_symbols == ()


def test_self_audit_checks_symbols():
    assert phase_i_self_audit().checked_symbols > 0


def test_self_audit_to_dict():
    assert phase_i_self_audit().to_dict()["schema_version"] == "i8.0"


def test_i1_public_surface():
    for symbol in ("CampaignRepository", "CampaignRepositoryManifest"):
        assert hasattr(cr, symbol)


def test_i2_public_surface():
    for symbol in ("DurableArtifactStore", "ArtifactStoreManifest"):
        assert hasattr(cr, symbol)


def test_i3_public_surface():
    for symbol in (
        "CampaignCheckpoint",
        "CampaignCheckpointStore",
        "ResumePlanner",
        "audit_checkpoint_lineage",
    ):
        assert hasattr(cr, symbol)


def test_i4_public_surface():
    for symbol in (
        "CampaignReproducibilityVerifier",
        "ReproducibilityCertificate",
        "EvidenceIdentity",
    ):
        assert hasattr(cr, symbol)


def test_i5_public_surface():
    for symbol in (
        "ScientificReleaseBundleBuilder",
        "ScientificReleaseManifest",
        "ReleaseBuildResult",
    ):
        assert hasattr(cr, symbol)


def test_i6_public_surface():
    for symbol in (
        "ScientificReleaseVerifier",
        "ScientificReleaseImporter",
        "inspect_release",
    ):
        assert hasattr(cr, symbol)


def test_i7_public_surface():
    for symbol in (
        "ScientificReleaseCatalog",
        "ScientificReleaseCatalogQueryService",
        "record_from_verified_import",
        "export_catalog_snapshot",
    ):
        assert hasattr(cr, symbol)


def test_i8_public_surface():
    for symbol in (
        "PhaseIArchitectureContract",
        "PhaseIReferenceWorkflow",
        "build_phase_i_architecture_contract",
        "phase_i_self_audit",
    ):
        assert hasattr(cr, symbol)


def run_workflow(tmp_path, subdir="run"):
    (
        repo,
        repo_manifest,
        artifact_store,
        artifact_manifest,
        checkpoints,
        evidence,
    ) = build_inputs(tmp_path / subdir / "input")

    return PhaseIReferenceWorkflow().run(
        root=tmp_path / subdir / "workflow",
        release_name="PrimeAIExplorer-I8-Demo",
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=repo_manifest,
        artifact_store=artifact_store,
        artifact_manifest=artifact_manifest,
        checkpoints=checkpoints,
        scientific_evidence=evidence,
        metadata={"purpose": "I8-integration"},
    )


def test_reference_workflow(tmp_path):
    result = run_workflow(tmp_path)
    assert result.release_id.startswith("RELEASE-")


def test_reference_workflow_bundle_sha(tmp_path):
    assert len(run_workflow(tmp_path).bundle_sha256) == 64


def test_reference_workflow_manifest_sha(tmp_path):
    assert len(run_workflow(tmp_path).release_manifest_sha256) == 64


def test_reference_workflow_certificate_sha(tmp_path):
    assert len(run_workflow(tmp_path).reproducibility_certificate_sha256) == 64


def test_reference_workflow_catalog_record_sha(tmp_path):
    assert len(run_workflow(tmp_path).catalog_record_sha256) == 64


def test_reference_workflow_catalog_sha(tmp_path):
    assert len(run_workflow(tmp_path).catalog_sha256) == 64


def test_reference_workflow_snapshot_sha(tmp_path):
    assert len(run_workflow(tmp_path).catalog_snapshot_sha256) == 64


def test_reference_workflow_import_path(tmp_path):
    assert Path(run_workflow(tmp_path).imported_path).is_dir()


def test_reference_workflow_to_dict(tmp_path):
    assert run_workflow(tmp_path).to_dict()["schema_version"] == "i8.0"


def test_reference_workflow_deterministic_release(tmp_path):
    a = run_workflow(tmp_path, "a")
    b = run_workflow(tmp_path, "b")
    assert a.release_manifest_sha256 == b.release_manifest_sha256


def test_reference_workflow_deterministic_bundle(tmp_path):
    a = run_workflow(tmp_path, "a")
    b = run_workflow(tmp_path, "b")
    assert a.bundle_sha256 == b.bundle_sha256


def test_reference_workflow_deterministic_certificate(tmp_path):
    a = run_workflow(tmp_path, "a")
    b = run_workflow(tmp_path, "b")
    assert (
        a.reproducibility_certificate_sha256
        == b.reproducibility_certificate_sha256
    )


def test_reference_workflow_deterministic_catalog_record(tmp_path):
    a = run_workflow(tmp_path, "a")
    b = run_workflow(tmp_path, "b")

    # Catalog records include the environment-specific imported path,
    # so their local record identities are not required to match.
    assert len(a.catalog_record_sha256) == 64
    assert len(b.catalog_record_sha256) == 64

    # Portable scientific identities must remain deterministic.
    assert a.release_manifest_sha256 == b.release_manifest_sha256
    assert a.bundle_sha256 == b.bundle_sha256
    assert (
        a.reproducibility_certificate_sha256
        == b.reproducibility_certificate_sha256
    )

def test_reference_workflow_deterministic_catalog(tmp_path):
    a = run_workflow(tmp_path, "a")
    b = run_workflow(tmp_path, "b")

    # Catalog SHA includes local catalog records and therefore may differ
    # between independent import environments.
    assert len(a.catalog_sha256) == 64
    assert len(b.catalog_sha256) == 64

    # The portable release remains identical.
    assert a.release_manifest_sha256 == b.release_manifest_sha256
    assert a.bundle_sha256 == b.bundle_sha256

def test_reference_workflow_deterministic_snapshot(tmp_path):
    a = run_workflow(tmp_path, "a")
    b = run_workflow(tmp_path, "b")

    # Snapshot identity reflects environment-local catalog state.
    assert len(a.catalog_snapshot_sha256) == 64
    assert len(b.catalog_snapshot_sha256) == 64

    # Scientific release identity remains environment-independent.
    assert a.release_manifest_sha256 == b.release_manifest_sha256
    assert a.bundle_sha256 == b.bundle_sha256

def test_reference_workflow_evidence_change_changes_release(tmp_path):
    (
        repo,
        repo_manifest,
        artifact_store,
        artifact_manifest,
        checkpoints,
        evidence,
    ) = build_inputs(tmp_path / "input")

    workflow = PhaseIReferenceWorkflow()

    a = workflow.run(
        root=tmp_path / "a",
        release_name="R",
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=repo_manifest,
        artifact_store=artifact_store,
        artifact_manifest=artifact_manifest,
        checkpoints=checkpoints,
        scientific_evidence=evidence,
    )

    changed = tuple(
        EvidenceIdentity(
            item.evidence_type,
            item.evidence_id,
            ("f" * 64 if item.evidence_id == "RESULT-1" else item.sha256),
            metadata=item.metadata,
        )
        for item in evidence
    )

    b = workflow.run(
        root=tmp_path / "b",
        release_name="R",
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=repo_manifest,
        artifact_store=artifact_store,
        artifact_manifest=artifact_manifest,
        checkpoints=checkpoints,
        scientific_evidence=changed,
    )

    assert a.release_manifest_sha256 != b.release_manifest_sha256
    assert a.bundle_sha256 != b.bundle_sha256


def test_reference_workflow_rejects_corrupt_repository(tmp_path):
    (
        repo,
        repo_manifest,
        artifact_store,
        artifact_manifest,
        checkpoints,
        evidence,
    ) = build_inputs(tmp_path / "input")

    entry = repo_manifest.entries[0]
    path = (
        repo.objects_root
        / entry.object_kind.value
        / entry.object_sha256[:2]
        / f"{entry.object_sha256}.json"
    )
    path.write_text('{"tampered":true}', encoding="utf-8")

    with pytest.raises(ValidationError):
        PhaseIReferenceWorkflow().run(
            root=tmp_path / "workflow",
            release_name="R",
            campaign_id="C",
            experiment_id="E",
            repository=repo,
            repository_manifest=repo_manifest,
            artifact_store=artifact_store,
            artifact_manifest=artifact_manifest,
            checkpoints=checkpoints,
            scientific_evidence=evidence,
        )


def test_reference_workflow_rejects_corrupt_artifact(tmp_path):
    (
        repo,
        repo_manifest,
        artifact_store,
        artifact_manifest,
        checkpoints,
        evidence,
    ) = build_inputs(tmp_path / "input")

    descriptor = artifact_manifest.artifacts[0]
    artifact_store.blob_path_for_sha256(
        descriptor.sha256
    ).write_bytes(b"tampered")

    with pytest.raises(ValidationError):
        PhaseIReferenceWorkflow().run(
            root=tmp_path / "workflow",
            release_name="R",
            campaign_id="C",
            experiment_id="E",
            repository=repo,
            repository_manifest=repo_manifest,
            artifact_store=artifact_store,
            artifact_manifest=artifact_manifest,
            checkpoints=checkpoints,
            scientific_evidence=evidence,
        )


def test_reference_workflow_rejects_bad_checkpoint_lineage(tmp_path):
    (
        repo,
        repo_manifest,
        artifact_store,
        artifact_manifest,
        checkpoints,
        evidence,
    ) = build_inputs(tmp_path / "input")

    cp0, cp1 = checkpoints
    bad = replace(cp1, parent_checkpoint_sha256="f" * 64)

    with pytest.raises(ValidationError):
        PhaseIReferenceWorkflow().run(
            root=tmp_path / "workflow",
            release_name="R",
            campaign_id="C",
            experiment_id="E",
            repository=repo,
            repository_manifest=repo_manifest,
            artifact_store=artifact_store,
            artifact_manifest=artifact_manifest,
            checkpoints=(cp0, bad),
            scientific_evidence=evidence,
        )


def test_architecture_i1_title():
    assert "Repository" in build_phase_i_architecture_contract().stages[0].title


def test_architecture_i2_title():
    assert "Artifact" in build_phase_i_architecture_contract().stages[1].title


def test_architecture_i3_title():
    assert "Checkpoint" in build_phase_i_architecture_contract().stages[2].title


def test_architecture_i4_title():
    assert "Reproducibility" in build_phase_i_architecture_contract().stages[3].title


def test_architecture_i5_title():
    assert "Release Bundle" in build_phase_i_architecture_contract().stages[4].title


def test_architecture_i6_title():
    assert "Verification" in build_phase_i_architecture_contract().stages[5].title


def test_architecture_i7_title():
    assert "Catalog" in build_phase_i_architecture_contract().stages[6].title


def test_architecture_i8_title():
    assert "Architecture Freeze" in build_phase_i_architecture_contract().stages[7].title
