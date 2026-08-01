from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from reproducibility_bundle import build_bundle, verify_bundle


def test_build_and_verify_bundle(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "run"
    source.mkdir(parents=True)
    (source / "responses.jsonl").write_text('{"prediction":6}\n', encoding="utf-8")
    (source / "analysis.json").write_text('{"accuracy":1.0}\n', encoding="utf-8")

    result = build_bundle(
        project_root=project,
        output_root=tmp_path / "bundles",
        bundle_name="demo",
        sources=[Path("run")],
        command=["py", "-m", "end_to_end_pipeline.cli", "run", "spec.json"],
        metadata={"experiment_id": "EXP-DEMO"},
    )

    assert result.artifact_count == 2
    assert result.archive_path is not None
    assert result.archive_path.exists()
    assert verify_bundle(result.bundle_root)["success"] is True


def test_tamper_detection(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "run"
    source.mkdir(parents=True)
    (source / "result.txt").write_text("original", encoding="utf-8")

    result = build_bundle(
        project_root=project,
        output_root=tmp_path / "bundles",
        bundle_name="tamper",
        sources=[Path("run")],
        create_archive=False,
    )

    copied = result.bundle_root / "artifacts" / "run" / "result.txt"
    copied.write_text("modified", encoding="utf-8")

    verification = verify_bundle(result.bundle_root)
    assert verification["success"] is False
    assert verification["records"][0]["sha256_match"] is False


def test_refuses_overwrite_by_default(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "run"
    source.mkdir(parents=True)
    (source / "x.txt").write_text("x", encoding="utf-8")

    kwargs = dict(
        project_root=project,
        output_root=tmp_path / "bundles",
        bundle_name="fixed",
        sources=[Path("run")],
        create_archive=False,
    )
    build_bundle(**kwargs)
    with pytest.raises(FileExistsError):
        build_bundle(**kwargs)


def test_manifest_has_sorted_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "run"
    source.mkdir(parents=True)
    (source / "z.txt").write_text("z", encoding="utf-8")
    (source / "a.txt").write_text("a", encoding="utf-8")

    result = build_bundle(
        project_root=project,
        output_root=tmp_path / "bundles",
        bundle_name="sorted",
        sources=[Path("run")],
        create_archive=False,
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    paths = [item["relative_path"] for item in manifest["artifacts"]]
    assert paths == sorted(paths)


def test_archive_has_fixed_timestamps(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "run"
    source.mkdir(parents=True)
    (source / "x.txt").write_text("x", encoding="utf-8")

    result = build_bundle(
        project_root=project,
        output_root=tmp_path / "bundles",
        bundle_name="archive",
        sources=[Path("run")],
    )
    with zipfile.ZipFile(result.archive_path) as archive:
        assert all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in archive.infolist())


def test_cli_module_importable() -> None:
    import reproducibility_bundle.cli  # noqa: F401
