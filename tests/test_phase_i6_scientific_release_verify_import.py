from pathlib import Path
import json
import shutil
import zipfile

import pytest

from campaign_repository import (
    EvidenceIdentity,
    ScientificReleaseBundleBuilder,
    ScientificReleaseImporter,
    ScientificReleaseVerifier,
    inspect_release,
)
from kernel.exceptions import ValidationError


def build_release(tmp_path, *, sha="1" * 64):
    return ScientificReleaseBundleBuilder().build(
        output_dir=tmp_path / "out",
        release_name="i6-test-release",
        campaign_id="C",
        experiment_id="E",
        scientific_evidence=(
            EvidenceIdentity(
                "h6.result_set",
                "RESULT",
                sha,
            ),
        ),
        metadata={
            "phase": "I6",
        },
    )


def rewrite_zip(source: Path, destination: Path, mutate):
    with zipfile.ZipFile(source, "r") as zin:
        entries = {
            name: zin.read(name)
            for name in zin.namelist()
        }

    entries = mutate(entries)

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as zout:
        for name in sorted(entries):
            zout.writestr(name, entries[name])


def test_verify_valid_bundle(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(release.bundle_path)
    assert result.valid


def test_verify_bundle_sha(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(
        release.bundle_path,
        expected_bundle_sha256=release.bundle_sha256,
    )
    assert result.valid


def test_verify_wrong_bundle_sha(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(
        release.bundle_path,
        expected_bundle_sha256="0" * 64,
    )
    assert not result.valid
    assert "bundle_sha256_mismatch" in result.errors


def test_verify_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        ScientificReleaseVerifier().verify(tmp_path / "missing.zip")


def test_verify_invalid_zip(tmp_path):
    path = tmp_path / "bad.zip"
    path.write_bytes(b"not-a-zip")
    result = ScientificReleaseVerifier().verify(path)
    assert not result.valid
    assert "invalid_zip" in result.errors


def test_verify_reports_release_id(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(release.bundle_path)
    assert result.release_id == release.manifest.release_id


def test_verify_reports_manifest_sha(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(release.bundle_path)
    assert result.release_manifest_sha256 == release.manifest.release_manifest_sha256


def test_verify_checks_component(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(release.bundle_path)
    assert result.checked_entries == 2


def test_tampered_component_fails(tmp_path):
    release = build_release(tmp_path)
    bad = tmp_path / "tampered.zip"

    def mutate(entries):
        entries["manifests/scientific_evidence.json"] = b'{"tampered":true}'
        return entries

    rewrite_zip(Path(release.bundle_path), bad, mutate)
    result = ScientificReleaseVerifier().verify(bad)
    assert not result.valid
    assert any("component_sha256_mismatch" in x for x in result.errors)


def test_tampered_manifest_fails(tmp_path):
    release = build_release(tmp_path)
    bad = tmp_path / "tampered-manifest.zip"

    def mutate(entries):
        manifest = json.loads(entries["release/manifest.json"])
        manifest["release_name"] = "changed"
        entries["release/manifest.json"] = json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return entries

    rewrite_zip(Path(release.bundle_path), bad, mutate)
    result = ScientificReleaseVerifier().verify(bad)
    assert not result.valid
    assert "release_manifest_sha256_mismatch" in result.errors


def test_missing_manifest_fails(tmp_path):
    release = build_release(tmp_path)
    bad = tmp_path / "missing-manifest.zip"

    def mutate(entries):
        entries.pop("release/manifest.json")
        return entries

    rewrite_zip(Path(release.bundle_path), bad, mutate)
    result = ScientificReleaseVerifier().verify(bad)
    assert not result.valid
    assert any("missing_required_file:release/manifest.json" == x for x in result.errors)


def test_missing_index_fails(tmp_path):
    release = build_release(tmp_path)
    bad = tmp_path / "missing-index.zip"

    def mutate(entries):
        entries.pop("release/index.json")
        return entries

    rewrite_zip(Path(release.bundle_path), bad, mutate)
    result = ScientificReleaseVerifier().verify(bad)
    assert not result.valid


def test_missing_checksums_fails(tmp_path):
    release = build_release(tmp_path)
    bad = tmp_path / "missing-checksums.zip"

    def mutate(entries):
        entries.pop("release/checksums.sha256")
        return entries

    rewrite_zip(Path(release.bundle_path), bad, mutate)
    result = ScientificReleaseVerifier().verify(bad)
    assert not result.valid


def test_checksum_tampering_fails(tmp_path):
    release = build_release(tmp_path)
    bad = tmp_path / "bad-checksum.zip"

    def mutate(entries):
        text = entries["release/checksums.sha256"].decode()
        text = text.replace(text[:64], "0" * 64, 1)
        entries["release/checksums.sha256"] = text.encode()
        return entries

    rewrite_zip(Path(release.bundle_path), bad, mutate)
    result = ScientificReleaseVerifier().verify(bad)
    assert not result.valid


def test_index_release_id_tamper_fails(tmp_path):
    release = build_release(tmp_path)
    bad = tmp_path / "bad-index.zip"

    def mutate(entries):
        index = json.loads(entries["release/index.json"])
        index["release_id"] = "OTHER"
        entries["release/index.json"] = json.dumps(
            index,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return entries

    rewrite_zip(Path(release.bundle_path), bad, mutate)
    result = ScientificReleaseVerifier().verify(bad)
    assert not result.valid
    assert "index_release_id_mismatch" in result.errors


def test_import_valid_release(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path
    )
    assert result.imported_entries >= 3


def test_import_destination_exists(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path
    )
    assert Path(result.destination_path).is_dir()


def test_import_marker_exists(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path
    )
    marker = Path(result.destination_path) / "release" / "import.json"
    assert marker.is_file()


def test_import_idempotent(tmp_path):
    release = build_release(tmp_path)
    importer = ScientificReleaseImporter(tmp_path / "import")
    first = importer.import_bundle(release.bundle_path)
    second = importer.import_bundle(release.bundle_path)
    assert second.imported_entries == 0
    assert second.skipped_entries == first.imported_entries


def test_import_rejects_invalid_bundle(tmp_path):
    path = tmp_path / "bad.zip"
    path.write_bytes(b"bad")
    with pytest.raises(ValidationError):
        ScientificReleaseImporter(tmp_path / "import").import_bundle(path)


def test_import_expected_sha(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path,
        expected_bundle_sha256=release.bundle_sha256,
    )
    assert result.bundle_sha256 == release.bundle_sha256


def test_import_wrong_expected_sha(tmp_path):
    release = build_release(tmp_path)
    with pytest.raises(ValidationError):
        ScientificReleaseImporter(tmp_path / "import").import_bundle(
            release.bundle_path,
            expected_bundle_sha256="0" * 64,
        )


def test_import_conflict_rejected(tmp_path):
    release = build_release(tmp_path)
    importer = ScientificReleaseImporter(tmp_path / "import")
    result = importer.import_bundle(release.bundle_path)

    target = (
        Path(result.destination_path)
        / "release"
        / "index.json"
    )
    target.write_bytes(b"conflict")

    with pytest.raises(ValidationError):
        importer.import_bundle(release.bundle_path)


def test_import_preserves_component_bytes(tmp_path):
    release = build_release(tmp_path)
    importer = ScientificReleaseImporter(tmp_path / "import")
    result = importer.import_bundle(release.bundle_path)

    with zipfile.ZipFile(release.bundle_path) as zf:
        expected = zf.read("release/manifest.json")

    actual = (
        Path(result.destination_path)
        / "release"
        / "manifest.json"
    ).read_bytes()

    assert actual == expected


def test_inspect_valid_release(tmp_path):
    release = build_release(tmp_path)
    inspection = inspect_release(release.bundle_path)
    assert inspection.release_id == release.manifest.release_id


def test_inspect_component_count(tmp_path):
    release = build_release(tmp_path)
    inspection = inspect_release(release.bundle_path)
    assert inspection.component_count == release.manifest.component_count


def test_inspect_invalid_release(tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"bad")
    with pytest.raises(ValidationError):
        inspect_release(bad)


def test_inspection_to_dict(tmp_path):
    release = build_release(tmp_path)
    payload = inspect_release(release.bundle_path).to_dict()
    assert payload["schema_version"] == "i6.0"


def test_verification_to_dict(tmp_path):
    release = build_release(tmp_path)
    payload = ScientificReleaseVerifier().verify(
        release.bundle_path
    ).to_dict()
    assert payload["schema_version"] == "i6.0"


def test_import_result_to_dict(tmp_path):
    release = build_release(tmp_path)
    payload = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path
    ).to_dict()
    assert payload["schema_version"] == "i6.0"


def test_changed_release_gets_new_import_directory(tmp_path):
    a = build_release(tmp_path / "a", sha="1" * 64)
    b = build_release(tmp_path / "b", sha="2" * 64)

    importer = ScientificReleaseImporter(tmp_path / "import")
    ia = importer.import_bundle(a.bundle_path)
    ib = importer.import_bundle(b.bundle_path)

    assert ia.release_id != ib.release_id
    assert ia.destination_path != ib.destination_path


def test_safe_target_rejects_parent(tmp_path):
    importer = ScientificReleaseImporter(tmp_path)
    with pytest.raises(ValidationError):
        importer._safe_target(tmp_path / "dest", "../escape")


def test_safe_target_accepts_relative(tmp_path):
    importer = ScientificReleaseImporter(tmp_path)
    target = importer._safe_target(
        tmp_path / "dest",
        "release/index.json",
    )
    assert target.name == "index.json"


def test_manifest_checksum_verified(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(
        release.bundle_path
    )
    assert result.valid


def test_release_verifier_deterministic(tmp_path):
    release = build_release(tmp_path)
    verifier = ScientificReleaseVerifier()
    a = verifier.verify(release.bundle_path)
    b = verifier.verify(release.bundle_path)
    assert a.to_dict() == b.to_dict()


def test_import_same_bundle_sha(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path
    )
    assert result.bundle_sha256 == release.bundle_sha256


def test_import_release_id_matches_manifest(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path
    )
    assert result.release_id == release.manifest.release_id


def test_inspection_manifest_sha_matches(tmp_path):
    release = build_release(tmp_path)
    inspection = inspect_release(release.bundle_path)
    assert (
        inspection.release_manifest_sha256
        == release.manifest.release_manifest_sha256
    )


def test_verify_component_count_positive(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(release.bundle_path)
    assert result.checked_entries > 0


def test_import_creates_release_manifest(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path
    )
    assert (
        Path(result.destination_path)
        / "release"
        / "manifest.json"
    ).is_file()


def test_import_creates_scientific_evidence(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseImporter(tmp_path / "import").import_bundle(
        release.bundle_path
    )
    assert (
        Path(result.destination_path)
        / "manifests"
        / "scientific_evidence.json"
    ).is_file()


def test_verify_index_manifest_sha(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(release.bundle_path)
    assert result.valid


def test_verify_component_checksum_consistency(tmp_path):
    release = build_release(tmp_path)
    result = ScientificReleaseVerifier().verify(release.bundle_path)
    assert not any("checksum_mismatch" in e for e in result.errors)


def test_import_rejects_corrupted_component(tmp_path):
    release = build_release(tmp_path)
    bad = tmp_path / "corrupt.zip"

    def mutate(entries):
        entries["manifests/scientific_evidence.json"] = b"corrupt"
        return entries

    rewrite_zip(Path(release.bundle_path), bad, mutate)

    with pytest.raises(ValidationError):
        ScientificReleaseImporter(tmp_path / "import").import_bundle(bad)
