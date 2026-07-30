from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from core.release_hardening import ReleaseHardening, stable_sha256


class PhaseETests(unittest.TestCase):
    def test_stable_hash(self):
        self.assertEqual(
            stable_sha256({"b": 2, "a": 1}),
            stable_sha256({"a": 1, "b": 2}),
        )

    def test_version_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "VERSION").write_text("1.3.0-rc1\n", encoding="utf-8")
            self.assertTrue(ReleaseHardening(root).validate_version()["valid"])

    def test_missing_required_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "VERSION").write_text("1.3.0-rc1\n", encoding="utf-8")
            self.assertTrue(ReleaseHardening(root).missing_required_files())

    def test_source_files_exclude_generated_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "core" / "x.py"
            source.parent.mkdir(parents=True)
            source.write_text("x=1\n", encoding="utf-8")
            generated = root / "experiments" / "EXP-000003" / "data" / "x.npy"
            generated.parent.mkdir(parents=True)
            generated.write_bytes(b"x")
            names = [
                p.relative_to(root).as_posix()
                for p in ReleaseHardening(root).source_files()
            ]
            self.assertIn("core/x.py", names)
            self.assertNotIn("experiments/EXP-000003/data/x.npy", names)

    def test_release_manifest_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "README.md"
            path.write_text("hello\n", encoding="utf-8")
            hardening = ReleaseHardening(root)
            self.assertEqual(
                hardening.release_manifest()["manifest_sha256"],
                hardening.release_manifest()["manifest_sha256"],
            )

    def test_deterministic_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("hello\n", encoding="utf-8")
            hardening = ReleaseHardening(root)
            manifest = hardening.release_manifest()
            one = hardening.build_zip(root / "a.zip", manifest)
            two = hardening.build_zip(root / "b.zip", manifest)
            self.assertEqual(one["archive_sha256"], two["archive_sha256"])

    def test_archive_contains_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("hello\n", encoding="utf-8")
            hardening = ReleaseHardening(root)
            manifest = hardening.release_manifest()
            archive = root / "release.zip"
            hardening.build_zip(archive, manifest)
            with zipfile.ZipFile(archive) as zf:
                self.assertTrue(any(
                    name.endswith("/release/release_manifest.json")
                    for name in zf.namelist()
                ))


if __name__ == "__main__":
    unittest.main()
