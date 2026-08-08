from dataclasses import replace
from pathlib import Path

import pytest

from campaign_repository import (
    ArtifactStoreManifest,
    CampaignCheckpoint,
    CampaignCheckpointStore,
    CampaignRepository,
    CampaignReproducibilityVerifier,
    CheckpointStatus,
    DurableArtifactStore,
    EvidenceIdentity,
    JobCheckpoint,
    ReproducibilityCertificate,
    ReproducibilityCertificateManifest,
    VerificationCheck,
    VerificationStatus,
    next_checkpoint,
)
from kernel.exceptions import ValidationError


def evidence(kind="h6.result_set", eid="RESULT-1", sha="a" * 64):
    return EvidenceIdentity(kind, eid, sha)


def test_evidence_identity():
    value = evidence()
    assert value.sha256 == "a" * 64


def test_evidence_requires_sha256():
    with pytest.raises(ValidationError):
        EvidenceIdentity("x", "y", "bad")


def test_evidence_lowercases_sha():
    value = EvidenceIdentity("x", "y", "A" * 64)
    assert value.sha256 == "a" * 64


def test_verification_check_passed():
    value = VerificationCheck(
        "check",
        VerificationStatus.PASSED,
        "ok",
    )
    assert value.passed


def test_verification_check_string_status():
    value = VerificationCheck("check", "passed", "ok")
    assert value.status == VerificationStatus.PASSED


def test_verification_check_bad_status():
    with pytest.raises(ValidationError):
        VerificationCheck("check", "bad", "oops")


def test_duplicate_evidence_rejected():
    e = evidence()
    with pytest.raises(ValidationError):
        VerificationCheck(
            "check",
            "passed",
            "ok",
            evidence=(e, e),
        )


def test_certificate_counts():
    cert = ReproducibilityCertificate(
        "CERT",
        "C",
        "E",
        (
            VerificationCheck("a", "passed", "ok"),
            VerificationCheck("b", "failed", "bad"),
            VerificationCheck("c", "skipped", "skip"),
        ),
    )
    assert cert.passed_count == 1
    assert cert.failed_count == 1
    assert cert.skipped_count == 1
    assert not cert.reproducible


def test_certificate_reproducible_without_failures():
    cert = ReproducibilityCertificate(
        "CERT",
        "C",
        "E",
        (
            VerificationCheck("a", "passed", "ok"),
            VerificationCheck("b", "skipped", "skip"),
        ),
    )
    assert cert.reproducible


def test_certificate_identity_stable():
    a = ReproducibilityCertificate(
        "CERT-A",
        "C",
        "E",
        (VerificationCheck("a", "passed", "ok"),),
    )
    b = ReproducibilityCertificate(
        "CERT-B",
        "C",
        "E",
        (VerificationCheck("a", "passed", "ok"),),
    )
    assert a.certificate_sha256 == b.certificate_sha256


def test_certificate_duplicate_checks():
    with pytest.raises(ValidationError):
        ReproducibilityCertificate(
            "CERT",
            "C",
            "E",
            (
                VerificationCheck("a", "passed", "ok"),
                VerificationCheck("a", "passed", "ok"),
            ),
        )


def build_repo(tmp_path):
    repo = CampaignRepository(tmp_path / "repo")
    result = repo.store_json(
        object_id="RESULT-1",
        object_kind="result_set",
        campaign_id="C",
        experiment_id="E",
        payload={"value": 1},
    )
    manifest = repo.build_manifest(
        repository_id="REPO",
        entries=(result.entry,),
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
    return store, manifest, a, b


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


def test_verifier_all_skipped():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
    )
    assert cert.reproducible
    assert cert.skipped_count == 4


def test_repository_verification_pass(tmp_path):
    repo, manifest = build_repo(tmp_path)
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=manifest,
    )
    check = next(x for x in cert.checks if x.check_id == "repository")
    assert check.status == VerificationStatus.PASSED


def test_repository_pair_required(tmp_path):
    repo, manifest = build_repo(tmp_path)
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
    )
    check = next(x for x in cert.checks if x.check_id == "repository")
    assert check.status == VerificationStatus.FAILED


def test_repository_corruption_fails(tmp_path):
    repo, manifest = build_repo(tmp_path)
    entry = manifest.entries[0]
    path = (
        repo.objects_root
        / entry.object_kind.value
        / entry.object_sha256[:2]
        / f"{entry.object_sha256}.json"
    )
    path.write_text('{"tampered":true}', encoding="utf-8")
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=manifest,
    )
    assert cert.failed_count == 1


def test_artifact_verification_pass(tmp_path):
    store, manifest, _, _ = build_artifacts(tmp_path)
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        artifact_store=store,
        artifact_manifest=manifest,
    )
    check = next(x for x in cert.checks if x.check_id == "artifacts")
    assert check.status == VerificationStatus.PASSED


def test_artifact_pair_required(tmp_path):
    store, manifest, _, _ = build_artifacts(tmp_path)
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        artifact_store=store,
    )
    check = next(x for x in cert.checks if x.check_id == "artifacts")
    assert check.status == VerificationStatus.FAILED


def test_artifact_corruption_fails(tmp_path):
    store, manifest, a, _ = build_artifacts(tmp_path)
    (store.root / a.blob_path).write_bytes(b"corrupt")
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        artifact_store=store,
        artifact_manifest=manifest,
    )
    check = next(x for x in cert.checks if x.check_id == "artifacts")
    assert check.status == VerificationStatus.FAILED


def test_checkpoint_verification_pass():
    cp0, cp1 = build_checkpoints()
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        checkpoints=(cp0, cp1),
    )
    check = next(x for x in cert.checks if x.check_id == "checkpoints")
    assert check.status == VerificationStatus.PASSED


def test_checkpoint_bad_parent_fails():
    cp0, cp1 = build_checkpoints()
    bad = replace(cp1, parent_checkpoint_sha256="f" * 64)
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        checkpoints=(cp0, bad),
    )
    check = next(x for x in cert.checks if x.check_id == "checkpoints")
    assert check.status == VerificationStatus.FAILED


def test_scientific_evidence_pass():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(
            evidence("h6.result_set", "R", "1" * 64),
            evidence("h6.provenance", "P", "2" * 64),
            evidence("h7.analysis", "A", "3" * 64),
            evidence("h8.publication", "O", "4" * 64),
        ),
    )
    check = next(x for x in cert.checks if x.check_id == "scientific_evidence")
    assert check.status == VerificationStatus.PASSED


def test_duplicate_scientific_evidence_fails():
    e1 = evidence("h6.result_set", "R", "1" * 64)
    e2 = evidence("h6.result_set", "R", "2" * 64)
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(e1, e2),
    )
    check = next(x for x in cert.checks if x.check_id == "scientific_evidence")
    assert check.status == VerificationStatus.FAILED


def test_full_certificate_pass(tmp_path):
    repo, rmanifest = build_repo(tmp_path)
    store, amanifest, _, _ = build_artifacts(tmp_path)
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
            evidence("h6.result_set", "R", "1" * 64),
            evidence("h6.provenance", "P", "2" * 64),
            evidence("h7.analysis", "A", "3" * 64),
            evidence("h8.publication", "O", "4" * 64),
        ),
    )
    assert cert.reproducible
    assert cert.passed_count == 4
    assert cert.failed_count == 0


def test_full_certificate_identity_stable(tmp_path):
    repo, rmanifest = build_repo(tmp_path)
    store, amanifest, _, _ = build_artifacts(tmp_path)
    cp0, cp1 = build_checkpoints()
    verifier = CampaignReproducibilityVerifier()
    a = verifier.verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=rmanifest,
        artifact_store=store,
        artifact_manifest=amanifest,
        checkpoints=(cp0, cp1),
    )
    b = verifier.verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=rmanifest,
        artifact_store=store,
        artifact_manifest=amanifest,
        checkpoints=(cp0, cp1),
    )
    assert a.certificate_sha256 == b.certificate_sha256


def test_certificate_id_stable(tmp_path):
    repo, rmanifest = build_repo(tmp_path)
    verifier = CampaignReproducibilityVerifier()
    a = verifier.verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=rmanifest,
    )
    b = verifier.verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=rmanifest,
    )
    assert a.certificate_id == b.certificate_id


def test_metadata_preserved():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        metadata={"phase": "I4"},
    )
    assert cert.metadata == {"phase": "I4"}


def test_certificate_to_dict():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
    )
    payload = cert.to_dict()
    assert payload["schema_version"] == "i4.0"
    assert len(payload["certificate_sha256"]) == 64


def test_certificate_manifest():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
    )
    manifest = ReproducibilityCertificateManifest.from_certificate(
        cert,
        source="unit-test",
    )
    assert manifest.certificate_sha256 == cert.certificate_sha256


def test_certificate_manifest_identity_stable():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
    )
    a = ReproducibilityCertificateManifest.from_certificate(
        cert,
        source="unit-test",
    )
    b = ReproducibilityCertificateManifest.from_certificate(
        cert,
        source="unit-test",
    )
    assert a.manifest_sha256 == b.manifest_sha256


def test_certificate_manifest_metadata():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
    )
    manifest = ReproducibilityCertificateManifest.from_certificate(
        cert,
        source="unit-test",
        metadata={"release": "candidate"},
    )
    assert manifest.metadata == {"release": "candidate"}


def test_certificate_manifest_to_dict():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
    )
    manifest = ReproducibilityCertificateManifest.from_certificate(
        cert,
        source="unit-test",
    )
    assert manifest.to_dict()["schema_version"] == "i4.0"


def test_repository_evidence_in_certificate(tmp_path):
    repo, manifest = build_repo(tmp_path)
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=manifest,
    )
    check = next(x for x in cert.checks if x.check_id == "repository")
    assert check.evidence[0].sha256 == manifest.manifest_sha256


def test_artifact_evidence_in_certificate(tmp_path):
    store, manifest, _, _ = build_artifacts(tmp_path)
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        artifact_store=store,
        artifact_manifest=manifest,
    )
    check = next(x for x in cert.checks if x.check_id == "artifacts")
    assert check.evidence[0].sha256 == manifest.manifest_sha256


def test_checkpoint_evidence_count():
    cp0, cp1 = build_checkpoints()
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        checkpoints=(cp0, cp1),
    )
    check = next(x for x in cert.checks if x.check_id == "checkpoints")
    assert len(check.evidence) == 2


def test_reproducible_false_on_any_failure(tmp_path):
    repo, manifest = build_repo(tmp_path)
    entry = manifest.entries[0]
    path = (
        repo.objects_root
        / entry.object_kind.value
        / entry.object_sha256[:2]
        / f"{entry.object_sha256}.json"
    )
    path.write_text("bad", encoding="utf-8")
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        repository=repo,
        repository_manifest=manifest,
    )
    assert not cert.reproducible


def test_skips_do_not_fail_reproducibility():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(evidence(),),
    )
    assert cert.reproducible
    assert cert.skipped_count == 3


def test_scientific_evidence_order_deterministic():
    a = evidence("h7.analysis", "A", "3" * 64)
    b = evidence("h6.result_set", "R", "1" * 64)
    cert1 = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(a, b),
    )
    cert2 = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(b, a),
    )
    assert cert1.certificate_sha256 == cert2.certificate_sha256


def test_check_order_deterministic():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
    )
    assert [x.check_id for x in cert.checks] == sorted(
        x.check_id for x in cert.checks
    )


def test_manifest_requires_certificate():
    with pytest.raises(ValidationError):
        ReproducibilityCertificateManifest.from_certificate(
            "bad",
            source="unit-test",
        )


def test_evidence_metadata():
    e = EvidenceIdentity(
        "h8.publication",
        "PUB",
        "f" * 64,
        metadata={"publisher": "g8"},
    )
    assert e.metadata == {"publisher": "g8"}


def test_verification_check_metadata():
    check = VerificationCheck(
        "check",
        "passed",
        "ok",
        metadata={"x": 1},
    )
    assert check.metadata == {"x": 1}


def test_certificate_manifest_reproducible_flag():
    cert = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
    )
    manifest = ReproducibilityCertificateManifest.from_certificate(
        cert,
        source="unit-test",
    )
    assert manifest.reproducible is True


def test_certificate_changes_if_evidence_changes():
    a = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(evidence(sha="1" * 64),),
    )
    b = CampaignReproducibilityVerifier().verify(
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(evidence(sha="2" * 64),),
    )
    assert a.certificate_sha256 != b.certificate_sha256
