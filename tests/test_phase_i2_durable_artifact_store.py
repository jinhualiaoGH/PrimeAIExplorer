from io import BytesIO
from pathlib import Path

import pytest

from campaign_repository import (
    ArtifactDescriptor,
    ArtifactIntegrityAudit,
    ArtifactStoreManifest,
    DurableArtifactStore,
    StoredArtifact,
    audit_artifact_manifest,
)
from kernel.exceptions import ValidationError


def test_store_initialize(tmp_path):
    store = DurableArtifactStore(tmp_path)
    store.initialize()
    assert (tmp_path / "blobs").is_dir()


def test_put_bytes(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="hello.bin")
    assert isinstance(stored, StoredArtifact)


def test_put_bytes_sha256(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="hello.bin")
    assert len(stored.descriptor.sha256) == 64


def test_put_bytes_size(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="hello.bin")
    assert stored.descriptor.size_bytes == 5


def test_put_bytes_path_layout(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="hello.bin")
    sha = stored.descriptor.sha256
    assert stored.blob_path == f"blobs/{sha[:2]}/{sha[2:4]}/{sha}"


def test_put_bytes_not_deduplicated_first_time(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="hello.bin")
    assert stored.deduplicated is False


def test_put_bytes_deduplicates(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"hello", name="a.bin")
    b = store.put_bytes(b"hello", name="b.bin")
    assert b.deduplicated is True
    assert a.blob_path == b.blob_path


def test_content_identity_ignores_name(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"same", name="alpha.txt")
    b = store.put_bytes(b"same", name="beta.txt")
    assert a.descriptor.sha256 == b.descriptor.sha256


def test_content_identity_changes_with_bytes(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"a", name="x")
    b = store.put_bytes(b"b", name="x")
    assert a.descriptor.sha256 != b.descriptor.sha256


def test_put_bytearray(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(bytearray(b"abc"), name="x")
    assert store.read_bytes(stored.descriptor) == b"abc"


def test_put_bytes_rejects_non_bytes(tmp_path):
    store = DurableArtifactStore(tmp_path)
    with pytest.raises(ValidationError):
        store.put_bytes("hello", name="x")


def test_put_stream(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_stream(BytesIO(b"stream"), name="stream.bin")
    assert store.read_bytes(stored.descriptor) == b"stream"


def test_put_stream_rejects_non_stream(tmp_path):
    store = DurableArtifactStore(tmp_path)
    with pytest.raises(ValidationError):
        store.put_stream(123, name="x")


def test_put_file(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"file-data")
    store = DurableArtifactStore(tmp_path / "store")
    stored = store.put_file(source)
    assert store.read_bytes(stored.descriptor) == b"file-data"


def test_put_file_missing(tmp_path):
    store = DurableArtifactStore(tmp_path / "store")
    with pytest.raises(FileNotFoundError):
        store.put_file(tmp_path / "missing.bin")


def test_put_file_guesses_media_type(tmp_path):
    source = tmp_path / "sample.json"
    source.write_text("{}", encoding="utf-8")
    store = DurableArtifactStore(tmp_path / "store")
    stored = store.put_file(source)
    assert stored.descriptor.media_type == "application/json"


def test_put_file_explicit_media_type(tmp_path):
    source = tmp_path / "sample.data"
    source.write_bytes(b"x")
    store = DurableArtifactStore(tmp_path / "store")
    stored = store.put_file(source, media_type="application/x-test")
    assert stored.descriptor.media_type == "application/x-test"


def test_read_bytes(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    assert store.read_bytes(stored.descriptor) == b"hello"


def test_open(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    with store.open(stored.descriptor) as handle:
        assert handle.read() == b"hello"


def test_verify_valid(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    verification = store.verify(stored.descriptor)
    assert verification.valid


def test_verify_missing(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    (tmp_path / stored.blob_path).unlink()
    verification = store.verify(stored.descriptor)
    assert not verification.exists
    assert not verification.valid


def test_verify_corruption(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    (tmp_path / stored.blob_path).write_bytes(b"corrupt")
    verification = store.verify(stored.descriptor)
    assert verification.exists
    assert not verification.valid


def test_read_detects_corruption(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    (tmp_path / stored.blob_path).write_bytes(b"corrupt")
    with pytest.raises(ValidationError):
        store.read_bytes(stored.descriptor)


def test_open_detects_corruption(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    (tmp_path / stored.blob_path).write_bytes(b"corrupt")
    with pytest.raises(ValidationError):
        store.open(stored.descriptor)


def test_existing_corrupt_content_address_rejected(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    path = tmp_path / stored.blob_path
    path.write_bytes(b"bad")
    with pytest.raises(ValidationError):
        store.put_bytes(b"hello", name="again")


def test_blob_path_rejects_bad_digest(tmp_path):
    store = DurableArtifactStore(tmp_path)
    with pytest.raises(ValidationError):
        store.blob_path_for_sha256("bad")


def test_chunk_size_validation(tmp_path):
    with pytest.raises(ValidationError):
        DurableArtifactStore(tmp_path, chunk_size=0)


def test_metadata_preserved(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(
        b"x",
        name="x",
        metadata={"campaign": "I2"},
    )
    assert stored.descriptor.metadata == {"campaign": "I2"}


def test_verify_many(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"a", name="a")
    b = store.put_bytes(b"b", name="b")
    results = store.verify_many((a.descriptor, b.descriptor))
    assert len(results) == 2
    assert all(item.valid for item in results)


def test_manifest_counts(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"same", name="a")
    b = store.put_bytes(b"same", name="b")
    manifest = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(a.descriptor, b.descriptor),
    )
    assert manifest.artifact_count == 2
    assert manifest.unique_blob_count == 1


def test_manifest_size_dedup(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"12345", name="a")
    b = store.put_bytes(b"12345", name="b")
    manifest = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(a.descriptor, b.descriptor),
    )
    assert manifest.logical_size_bytes == 10
    assert manifest.unique_size_bytes == 5


def test_manifest_identity_stable(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"a", name="a")
    b = store.put_bytes(b"b", name="b")
    m1 = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(a.descriptor, b.descriptor),
    )
    m2 = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(b.descriptor, a.descriptor),
    )
    assert m1.manifest_sha256 == m2.manifest_sha256


def test_manifest_rejects_duplicate_descriptor(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"a", name="a")
    with pytest.raises(ValidationError):
        ArtifactStoreManifest(
            store_id="STORE",
            artifacts=(a.descriptor, a.descriptor),
        )


def test_manifest_to_dict(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"a", name="a")
    manifest = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(a.descriptor,),
    )
    payload = manifest.to_dict()
    assert payload["schema_version"] == "i2.0"
    assert len(payload["manifest_sha256"]) == 64


def test_integrity_audit_valid(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"a", name="a")
    b = store.put_bytes(b"b", name="b")
    manifest = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(a.descriptor, b.descriptor),
    )
    audit = audit_artifact_manifest(store=store, manifest=manifest)
    assert isinstance(audit, ArtifactIntegrityAudit)
    assert audit.checked_count == 2
    assert audit.valid_count == 2
    assert audit.invalid_count == 0
    assert audit.valid


def test_integrity_audit_detects_corruption(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"a", name="a")
    manifest = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(a.descriptor,),
    )
    (tmp_path / a.blob_path).write_bytes(b"bad")
    audit = audit_artifact_manifest(store=store, manifest=manifest)
    assert audit.invalid_count == 1
    assert not audit.valid


def test_integrity_audit_to_dict(tmp_path):
    store = DurableArtifactStore(tmp_path)
    a = store.put_bytes(b"a", name="a")
    manifest = ArtifactStoreManifest(
        store_id="STORE",
        artifacts=(a.descriptor,),
    )
    audit = audit_artifact_manifest(store=store, manifest=manifest)
    assert audit.to_dict()["schema_version"] == "i2.0"


def test_descriptor_path_is_canonical(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"hello", name="x")
    bad = ArtifactDescriptor(
        name=stored.descriptor.name,
        media_type=stored.descriptor.media_type,
        sha256=stored.descriptor.sha256,
        size_bytes=stored.descriptor.size_bytes,
        relative_path="wrong/path",
    )
    verification = store.verify(bad)
    assert not verification.valid


def test_stored_artifact_to_dict(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"x", name="x")
    assert stored.to_dict()["descriptor"]["name"] == "x"


def test_zero_length_artifact(tmp_path):
    store = DurableArtifactStore(tmp_path)
    stored = store.put_bytes(b"", name="empty.bin")
    assert stored.descriptor.size_bytes == 0
    assert store.verify(stored.descriptor).valid


def test_large_chunked_file(tmp_path):
    source = tmp_path / "large.bin"
    payload = b"abcdefghij" * 10000
    source.write_bytes(payload)
    store = DurableArtifactStore(tmp_path / "store", chunk_size=257)
    stored = store.put_file(source)
    assert store.read_bytes(stored.descriptor) == payload


def test_same_file_reingest_deduplicates(tmp_path):
    source = tmp_path / "data.bin"
    source.write_bytes(b"reingest")
    store = DurableArtifactStore(tmp_path / "store")
    first = store.put_file(source)
    second = store.put_file(source)
    assert first.deduplicated is False
    assert second.deduplicated is True
