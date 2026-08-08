from dataclasses import replace
import json
from pathlib import Path
import zipfile

import pytest

from campaign_repository import (
    ArtifactStoreManifest,
    CampaignCheckpoint,
    CampaignRepository,
    CampaignReproducibilityVerifier,
    CheckpointStatus,
    DurableArtifactStore,
    EvidenceIdentity,
    JobCheckpoint,
    ReleaseBuildResult,
    ReleaseComponent,
    ReleaseComponentKind,
    ScientificReleaseBundleBuilder,
    ScientificReleaseManifest,
    VerificationCheck,
    ReproducibilityCertificate,
    next_checkpoint,
)
from kernel.exceptions import ValidationError


def build_repo(tmp_path):
    repo = CampaignRepository(tmp_path / "repo")
    stored = repo.store_json(
        object_id="RESULT-1",
        object_kind="result_set",
        campaign_id="C",
        experiment_id="E",
        payload={"value": 1},
    )
    manifest = repo.build_manifest(
        repository_id="REPO",
        entries=(stored.entry,),
    )
    repo.write_manifest(manifest)
    return repo, manifest


def build_artifacts(tmp_path):
    store = DurableArtifactStore(tmp_path / "artifacts")
    a = store.put_bytes(b"a", name="a.bin")
    b = store.put_bytes(b"b", name="b.bin")
    manifest = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(a.descriptor, b.descriptor),
    )
    return store, manifest


def build_checkpoints():
    cp0 = CampaignCheckpoint(
        checkpoint_id="CP0",
        campaign_id="C",
        experiment_id="E",
        execution_plan_sha256="p" * 64,
        checkpoint_sequence=0,
        status=CheckpointStatus.INTERRUPTED,
        jobs=(
            JobCheckpoint("J1", True, 1, result_sha256="1" * 64),
            JobCheckpoint("J2", False, 0),
        ),
    )
    cp1 = next_checkpoint(
        cp0,
        status=CheckpointStatus.COMPLETED,
        jobs=(
            cp0.jobs[0],
            JobCheckpoint("J2", True, 1, result_sha256="2" * 64),
        ),
    )
    return cp0, cp1


def build_certificate(tmp_path):
    repo, rmanifest = build_repo(tmp_path)
    store, amanifest = build_artifacts(tmp_path)
    cp0, cp1 = build_checkpoints()
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=rmanifest,
        artifact_store=store,
        artifact_manifest=amanifest,
        checkpoints=(cp0, cp1),
        scientific_evidence=(
            EvidenceIdentity("h6.result_set", "R", "1" * 64),
            EvidenceIdentity("h7.analysis", "A", "2" * 64),
        ),
    )
    return rmanifest, amanifest, (cp0, cp1), cert


def component():
    return ReleaseComponent(
        component_id="repository-manifest",
        kind=ReleaseComponentKind.REPOSITORY_MANIFEST,
        sha256="a" * 64,
        relative_path="manifests/repository.json",
    )


def test_component():
    value = component()
    assert value.kind == ReleaseComponentKind.REPOSITORY_MANIFEST


def test_component_accepts_string_kind():
    value = replace(component(), kind="repository_manifest")
    assert value.kind == ReleaseComponentKind.REPOSITORY_MANIFEST


def test_component_rejects_bad_kind():
    with pytest.raises(ValidationError):
        replace(component(), kind="bad")


def test_component_rejects_bad_sha():
    with pytest.raises(ValidationError):
        replace(component(), sha256="bad")


def test_component_rejects_absolute_path():
    with pytest.raises(ValidationError):
        replace(component(), relative_path="/absolute/file")


def test_component_rejects_parent_path():
    with pytest.raises(ValidationError):
        replace(component(), relative_path="../file")


def test_manifest_count():
    value = ScientificReleaseManifest(
        release_id="R",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        components=(component(),),
    )
    assert value.component_count == 1


def test_manifest_identity_stable():
    a = ScientificReleaseManifest(
        release_id="R1",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        components=(component(),),
    )
    b = ScientificReleaseManifest(
        release_id="R2",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        components=(component(),),
    )
    assert a.release_manifest_sha256 == b.release_manifest_sha256


def test_manifest_rejects_duplicate_ids():
    with pytest.raises(ValidationError):
        ScientificReleaseManifest(
            release_id="R",
            release_name="release",
            campaign_id="C",
            experiment_id="E",
            components=(
                component(),
                replace(
                    component(),
                    relative_path="other/path.json",
                    sha256="b" * 64,
                ),
            ),
        )


def test_manifest_rejects_duplicate_paths():
    with pytest.raises(ValidationError):
        ScientificReleaseManifest(
            release_id="R",
            release_name="release",
            campaign_id="C",
            experiment_id="E",
            components=(
                component(),
                replace(
                    component(),
                    component_id="other",
                    sha256="b" * 64,
                ),
            ),
        )


def test_manifest_to_dict():
    value = ScientificReleaseManifest(
        release_id="R",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        components=(component(),),
    )
    payload = value.to_dict()
    assert payload["schema_version"] == "i5.0"
    assert len(payload["release_manifest_sha256"]) == 64


def test_build_empty_release(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    assert Path(result.bundle_path).is_file()
    assert result.manifest.component_count == 0


def test_build_result_type(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    assert isinstance(result, ReleaseBuildResult)


def test_build_repository_component(tmp_path):
    _, manifest = build_repo(tmp_path)
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "out",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        repository_manifest=manifest,
    )
    kinds = {item.kind for item in result.manifest.components}
    assert ReleaseComponentKind.REPOSITORY_MANIFEST in kinds


def test_build_artifact_component(tmp_path):
    _, manifest = build_artifacts(tmp_path)
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "out",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        artifact_manifest=manifest,
    )
    kinds = {item.kind for item in result.manifest.components}
    assert ReleaseComponentKind.ARTIFACT_MANIFEST in kinds


def test_build_checkpoint_component(tmp_path):
    cp0, cp1 = build_checkpoints()
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        checkpoints=(cp0, cp1),
    )
    kinds = {item.kind for item in result.manifest.components}
    assert ReleaseComponentKind.CHECKPOINT_LINEAGE in kinds


def test_build_certificate_component(tmp_path):
    _, _, _, cert = build_certificate(tmp_path)
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "out",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        reproducibility_certificate=cert,
    )
    kinds = {item.kind for item in result.manifest.components}
    assert ReleaseComponentKind.REPRODUCIBILITY_CERTIFICATE in kinds


def test_build_scientific_evidence_component(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(
            EvidenceIdentity("h6.result_set", "R", "1" * 64),
        ),
    )
    kinds = {item.kind for item in result.manifest.components}
    assert ReleaseComponentKind.SCIENTIFIC_EVIDENCE in kinds


def test_build_metadata_component(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        metadata={"title": "demo"},
    )
    kinds = {item.kind for item in result.manifest.components}
    assert ReleaseComponentKind.RELEASE_METADATA in kinds


def test_release_name_rejects_slash(tmp_path):
    with pytest.raises(ValidationError):
        ScientificReleaseBundleBuilder().build(
            output_dir=tmp_path,
            release_name="../bad",
            campaign_id="C",
            experiment_id="E",
        )


def test_bundle_has_manifest(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    with zipfile.ZipFile(result.bundle_path) as zf:
        assert "release/manifest.json" in zf.namelist()


def test_bundle_has_index(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    with zipfile.ZipFile(result.bundle_path) as zf:
        assert "release/index.json" in zf.namelist()


def test_bundle_has_checksums(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    with zipfile.ZipFile(result.bundle_path) as zf:
        assert "release/checksums.sha256" in zf.namelist()


def test_bundle_entry_count(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    assert result.entry_count == 3


def test_bundle_sha_length(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    assert len(result.bundle_sha256) == 64


def test_bundle_deterministic(tmp_path):
    builder = ScientificReleaseBundleBuilder()
    a = builder.build(
        output_dir=tmp_path / "a",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        metadata={"b": 2, "a": 1},
    )
    b = builder.build(
        output_dir=tmp_path / "b",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        metadata={"a": 1, "b": 2},
    )
    assert a.bundle_sha256 == b.bundle_sha256
    assert Path(a.bundle_path).read_bytes() == Path(b.bundle_path).read_bytes()


def test_release_id_deterministic(tmp_path):
    builder = ScientificReleaseBundleBuilder()
    a = builder.build(
        output_dir=tmp_path / "a",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    b = builder.build(
        output_dir=tmp_path / "b",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    assert a.manifest.release_id == b.manifest.release_id


def test_evidence_order_deterministic(tmp_path):
    e1 = EvidenceIdentity("h7.analysis", "A", "2" * 64)
    e2 = EvidenceIdentity("h6.result_set", "R", "1" * 64)
    builder = ScientificReleaseBundleBuilder()
    a = builder.build(
        output_dir=tmp_path / "a",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(e1, e2),
    )
    b = builder.build(
        output_dir=tmp_path / "b",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(e2, e1),
    )
    assert a.bundle_sha256 == b.bundle_sha256


def test_checkpoint_order_deterministic(tmp_path):
    cp0, cp1 = build_checkpoints()
    builder = ScientificReleaseBundleBuilder()
    a = builder.build(
        output_dir=tmp_path / "a",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        checkpoints=(cp0, cp1),
    )
    b = builder.build(
        output_dir=tmp_path / "b",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        checkpoints=(cp1, cp0),
    )
    assert a.bundle_sha256 == b.bundle_sha256


def test_changed_evidence_changes_bundle(tmp_path):
    builder = ScientificReleaseBundleBuilder()
    a = builder.build(
        output_dir=tmp_path / "a",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(
            EvidenceIdentity("h6.result_set", "R", "1" * 64),
        ),
    )
    b = builder.build(
        output_dir=tmp_path / "b",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(
            EvidenceIdentity("h6.result_set", "R", "2" * 64),
        ),
    )
    assert a.bundle_sha256 != b.bundle_sha256


def test_changed_metadata_changes_bundle(tmp_path):
    builder = ScientificReleaseBundleBuilder()
    a = builder.build(
        output_dir=tmp_path / "a",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        metadata={"v": 1},
    )
    b = builder.build(
        output_dir=tmp_path / "b",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        metadata={"v": 2},
    )
    assert a.bundle_sha256 != b.bundle_sha256


def test_full_release(tmp_path):
    rmanifest, amanifest, checkpoints, cert = build_certificate(tmp_path)
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "release",
        release_name="primeaiexplorer-demo",
        campaign_id="C",
        experiment_id="E",
        repository_manifest=rmanifest,
        artifact_manifest=amanifest,
        checkpoints=checkpoints,
        reproducibility_certificate=cert,
        scientific_evidence=(
            EvidenceIdentity("h6.result_set", "R", "1" * 64),
            EvidenceIdentity("h6.provenance", "P", "2" * 64),
            EvidenceIdentity("h7.analysis", "A", "3" * 64),
            EvidenceIdentity("h8.publication", "O", "4" * 64),
        ),
        metadata={"version": "1"},
    )
    assert result.manifest.component_count == 6
    assert result.entry_count == 9


def test_full_release_index(tmp_path):
    rmanifest, amanifest, checkpoints, cert = build_certificate(tmp_path)
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "release",
        release_name="primeaiexplorer-demo",
        campaign_id="C",
        experiment_id="E",
        repository_manifest=rmanifest,
        artifact_manifest=amanifest,
        checkpoints=checkpoints,
        reproducibility_certificate=cert,
    )
    with zipfile.ZipFile(result.bundle_path) as zf:
        index = json.loads(zf.read("release/index.json"))
    assert index["release_id"] == result.manifest.release_id


def test_manifest_component_hash_matches_bytes(tmp_path):
    _, rmanifest = build_repo(tmp_path)
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "out",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        repository_manifest=rmanifest,
    )
    component = result.manifest.components[0]
    import hashlib
    with zipfile.ZipFile(result.bundle_path) as zf:
        data = zf.read(component.relative_path)
    assert hashlib.sha256(data).hexdigest() == component.sha256


def test_checksums_mentions_component(tmp_path):
    _, rmanifest = build_repo(tmp_path)
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "out",
        release_name="release",
        campaign_id="C",
        experiment_id="E",
        repository_manifest=rmanifest,
    )
    with zipfile.ZipFile(result.bundle_path) as zf:
        checksums = zf.read("release/checksums.sha256").decode("utf-8")
    component = result.manifest.components[0]
    assert component.sha256 in checksums
    assert component.relative_path in checksums


def test_zip_timestamps_fixed(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    with zipfile.ZipFile(result.bundle_path) as zf:
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in zf.infolist())


def test_build_same_path_idempotent(tmp_path):
    builder = ScientificReleaseBundleBuilder()
    a = builder.build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    b = builder.build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    assert a.bundle_path == b.bundle_path
    assert a.bundle_sha256 == b.bundle_sha256


def test_release_build_result_to_dict(tmp_path):
    result = ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path,
        release_name="release",
        campaign_id="C",
        experiment_id="E",
    )
    payload = result.to_dict()
    assert payload["manifest"]["schema_version"] == "i5.0"


def test_bad_repository_manifest_type(tmp_path):
    with pytest.raises(ValidationError):
        ScientificReleaseBundleBuilder().build(
            output_dir=tmp_path,
            release_name="release",
            campaign_id="C",
            experiment_id="E",
            repository_manifest="bad",
        )


def test_bad_artifact_manifest_type(tmp_path):
    with pytest.raises(ValidationError):
        ScientificReleaseBundleBuilder().build(
            output_dir=tmp_path,
            release_name="release",
            campaign_id="C",
            experiment_id="E",
            artifact_manifest="bad",
        )


def test_bad_checkpoint_type(tmp_path):
    with pytest.raises(ValidationError):
        ScientificReleaseBundleBuilder().build(
            output_dir=tmp_path,
            release_name="release",
            campaign_id="C",
            experiment_id="E",
            checkpoints=("bad",),
        )


def test_bad_certificate_type(tmp_path):
    with pytest.raises(ValidationError):
        ScientificReleaseBundleBuilder().build(
            output_dir=tmp_path,
            release_name="release",
            campaign_id="C",
            experiment_id="E",
            reproducibility_certificate="bad",
        )


def test_bad_evidence_type(tmp_path):
    with pytest.raises(ValidationError):
        ScientificReleaseBundleBuilder().build(
            output_dir=tmp_path,
            release_name="release",
            campaign_id="C",
            experiment_id="E",
            scientific_evidence=("bad",),
        )
