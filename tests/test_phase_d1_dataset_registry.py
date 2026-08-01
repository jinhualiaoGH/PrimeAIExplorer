from __future__ import annotations

import json

import pytest

from dataset_registry import (
    DatasetRegistry,
    DatasetSplit,
    ProvenanceRecord,
    validate_manifest,
    verify_artifacts,
)
from dataset_registry.builder import build_manifest
from dataset_registry.io import load_manifest, write_manifest


def make_dataset(tmp_path):
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    (dataset / "train.jsonl").write_text(
        '{"x":1}\n{"x":2}\n',
        encoding="utf-8",
    )
    (dataset / "test.jsonl").write_text(
        '{"x":3}\n',
        encoding="utf-8",
    )
    return dataset


def make_manifest(dataset):
    provenance = ProvenanceRecord(
        source_type="synthetic",
        source_reference="phase-d1-test",
        generated_by="pytest",
        generated_at_utc="2026-08-01T12:00:00Z",
        parameters={"seed": 1},
    )
    return build_manifest(
        dataset,
        name="Fixture Dataset",
        version="1.0.0",
        description="Test dataset.",
        sequence_type="fixture",
        provenance=provenance,
        artifact_paths=("train.jsonl", "test.jsonl"),
        splits=(
            DatasetSplit(
                name="train",
                artifact_paths=("train.jsonl",),
            ),
            DatasetSplit(
                name="test",
                artifact_paths=("test.jsonl",),
            ),
        ),
        media_types={
            "train.jsonl": "application/x-ndjson",
            "test.jsonl": "application/x-ndjson",
        },
        record_counts={
            "train.jsonl": 2,
            "test.jsonl": 1,
        },
    )


def test_manifest_id_is_deterministic(tmp_path):
    dataset = make_dataset(tmp_path)
    first = make_manifest(dataset)
    second = make_manifest(dataset)

    assert first.dataset_id == second.dataset_id
    assert first.dataset_id.startswith("DS-")


def test_manifest_round_trip_accepts_utf8_bom(tmp_path):
    dataset = make_dataset(tmp_path)
    manifest = make_manifest(dataset)
    path = tmp_path / "manifest.json"
    write_manifest(path, manifest)

    text = path.read_text(encoding="utf-8")
    path.write_text(text, encoding="utf-8-sig")

    loaded = load_manifest(path)
    assert loaded.to_dict() == manifest.to_dict()


def test_artifact_verification_detects_modification(tmp_path):
    dataset = make_dataset(tmp_path)
    manifest = make_manifest(dataset)

    initial = verify_artifacts(dataset, manifest)
    assert all(item["sha256_match"] for item in initial)

    (dataset / "test.jsonl").write_text(
        '{"x":999}\n',
        encoding="utf-8",
    )
    modified = verify_artifacts(dataset, manifest)

    assert modified[1]["sha256_match"] is False


def test_registry_registration_is_idempotent(tmp_path):
    dataset = make_dataset(tmp_path)
    manifest = make_manifest(dataset)
    registry = DatasetRegistry(tmp_path / "registry")

    first = registry.register(dataset, manifest)
    second = registry.register(dataset, manifest)

    assert first == second
    assert registry.get(manifest.dataset_id) == manifest
    assert len(registry.list()) == 1


def test_registry_rejects_tampered_dataset(tmp_path):
    dataset = make_dataset(tmp_path)
    manifest = make_manifest(dataset)
    (dataset / "train.jsonl").write_text(
        '{"tampered":true}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="artifact verification"):
        DatasetRegistry(tmp_path / "registry").register(
            dataset,
            manifest,
        )


def test_manifest_validation_detects_wrong_id(tmp_path):
    dataset = make_dataset(tmp_path)
    manifest = make_manifest(dataset)
    document = manifest.to_dict()
    document["dataset_id"] = "DS-0000000000000000"
    path = tmp_path / "wrong.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    wrong = load_manifest(path)

    errors = validate_manifest(wrong)

    assert errors
    assert "dataset_id mismatch" in errors[0]
