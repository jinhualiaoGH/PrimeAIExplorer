from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import fnmatch
import json
import os
import subprocess
import tempfile
import zipfile


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(fd)
    temp = Path(name)
    try:
        temp.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class ReleaseHardening:
    release_version = "1.3.0"
    release_candidate = "1.3.0-rc1"

    required_files = (
        "VERSION",
        "CHANGELOG.md",
        "README.md",
        "LICENSE",
        "requirements.txt",
        "run_experiment.py",
        "core/prime_value_cases.py",
        "core/prime_value_evaluation.py",
        "sequence_plugins/builtin/prime_value.py",
        "experiments/EXP-000003/config/experiment.json",
        "scripts/build_exp000003_dataset.py",
        "scripts/generate_exp000003_cases.py",
        "scripts/evaluate_exp000003_responses.py",
    )

    excluded = (
        ".git/*",
        "__pycache__/*",
        "*.pyc",
        "backups/*",
        "PrimeAIExplorer_v*/*",
        "experiments/*/data/*",
        "experiments/*/benchmark/*",
        "experiments/*/responses/*",
        "experiments/*/evaluations/*",
        "experiments/*/leaderboard/*",
        "release/*.zip",
        "release/*.tmp",
    )

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _run(self, *parts: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            parts,
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def git_status(self) -> dict[str, Any]:
        version = self._run("git", "--version")
        if version.returncode != 0:
            return {"available": False, "clean": None, "branch": None}
        status = self._run("git", "status", "--porcelain")
        branch = self._run("git", "rev-parse", "--abbrev-ref", "HEAD")
        return {
            "available": True,
            "clean": status.returncode == 0 and not status.stdout.strip(),
            "branch": branch.stdout.strip() if branch.returncode == 0 else None,
            "status_lines": status.stdout.splitlines(),
        }

    def validate_version(self) -> dict[str, Any]:
        installed = (self.root / "VERSION").read_text(
            encoding="utf-8"
        ).strip()
        return {
            "installed": installed,
            "expected": self.release_candidate,
            "valid": installed == self.release_candidate,
        }

    def missing_required_files(self) -> list[str]:
        return [
            item for item in self.required_files
            if not (self.root / item).is_file()
        ]

    def validate_dataset(self) -> dict[str, Any]:
        base = self.root / "experiments" / "EXP-000003" / "data"
        dataset = base / "prime_values.npy"
        metadata = base / "prime_values.metadata.json"
        if not dataset.exists() or not metadata.exists():
            return {"exists": False, "valid": False}
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        expected = payload.get("dataset_sha256") or payload.get("sha256")
        actual = file_sha256(dataset)
        return {
            "exists": True,
            "count": payload.get("count"),
            "dataset_sha256": actual,
            "valid": expected == actual and payload.get("count") == 100000001,
        }

    def validate_benchmark(self) -> dict[str, Any]:
        base = self.root / "experiments" / "EXP-000003" / "benchmark"
        manifest_path = base / "manifest.json"
        if not manifest_path.exists():
            return {"exists": False, "valid": False}
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stored = manifest.get("manifest_sha256")
        unsigned = dict(manifest)
        unsigned.pop("manifest_sha256", None)
        total = manifest.get("total_case_count")
        counts = {
            "public": len(list((base / "cases" / "public").glob("*.json"))),
            "private": len(list((base / "cases" / "private").glob("*.json"))),
            "prompts": len(list((base / "prompts" / "text").glob("*.txt"))),
        }
        return {
            "exists": True,
            "manifest_sha256": stored,
            "total_case_count": total,
            **counts,
            "valid": (
                stable_sha256(unsigned) == stored
                and total == 500
                and counts["public"] == total
                and counts["private"] == total
                and counts["prompts"] == total
            ),
        }

    def validate_evaluations(self) -> dict[str, Any]:
        root = self.root / "experiments" / "EXP-000003" / "evaluations"
        summaries = sorted(root.glob("*/summary.json")) if root.exists() else []
        entries = []
        valid = True
        for path in summaries:
            payload = json.loads(path.read_text(encoding="utf-8"))
            stored = payload.get("summary_sha256")
            unsigned = dict(payload)
            unsigned.pop("summary_sha256", None)
            hash_ok = stable_sha256(unsigned) == stored
            case_count = payload.get("overall", {}).get("case_count")
            valid = valid and hash_ok and case_count == 500
            entries.append({
                "model_id": payload.get("model_id"),
                "summary_sha256": stored,
                "hash_valid": hash_ok,
                "case_count": case_count,
            })
        return {
            "evaluation_count": len(entries),
            "entries": entries,
            "valid": valid,
        }

    def run_tests(self) -> dict[str, Any]:
        result = self._run(
            "py", "-m", "unittest", "discover", "-s", "tests", "-v"
        )
        return {
            "passed": result.returncode == 0,
            "return_code": result.returncode,
            "output_tail": (result.stdout + result.stderr).splitlines()[-25:],
        }

    def run_compile(self) -> dict[str, Any]:
        result = self._run("py", "-m", "compileall", "-q", ".")
        return {
            "passed": result.returncode == 0,
            "return_code": result.returncode,
        }

    def source_files(self) -> list[Path]:
        selected = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root).as_posix()
            if any(fnmatch.fnmatch(rel, pattern) for pattern in self.excluded):
                continue
            selected.append(path)
        return sorted(selected, key=lambda p: p.relative_to(self.root).as_posix())

    def release_manifest(self) -> dict[str, Any]:
        records = [
            {
                "path": path.relative_to(self.root).as_posix(),
                "size": path.stat().st_size,
                "sha256": file_sha256(path),
            }
            for path in self.source_files()
        ]
        manifest = {
            "schema_version": "1.0",
            "release_version": self.release_version,
            "release_candidate": self.release_candidate,
            "file_count": len(records),
            "files": records,
        }
        manifest["manifest_sha256"] = stable_sha256(manifest)
        return manifest

    def build_zip(self, destination: Path, manifest: dict[str, Any]) -> dict[str, Any]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_suffix(".tmp")
        temp.unlink(missing_ok=True)
        prefix = f"PrimeAIExplorer-{self.release_version}/"

        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for record in manifest["files"]:
                source = self.root / record["path"]
                info = zipfile.ZipInfo(prefix + record["path"])
                info.date_time = (1980, 1, 1, 0, 0, 0)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                zf.writestr(info, source.read_bytes())

            info = zipfile.ZipInfo(prefix + "release/release_manifest.json")
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(
                info,
                (json.dumps(manifest, indent=2) + "\n").encode("utf-8"),
            )

        os.replace(temp, destination)
        return {
            "archive": str(destination),
            "archive_size": destination.stat().st_size,
            "archive_sha256": file_sha256(destination),
        }

    def acceptance(self, run_tests: bool = True) -> dict[str, Any]:
        report = {
            "schema_version": "1.0",
            "release_version": self.release_version,
            "release_candidate": self.release_candidate,
            "version": self.validate_version(),
            "missing_required_files": self.missing_required_files(),
            "dataset": self.validate_dataset(),
            "benchmark": self.validate_benchmark(),
            "evaluations": self.validate_evaluations(),
            "git": self.git_status(),
            "compile": self.run_compile(),
        }
        if run_tests:
            report["tests"] = self.run_tests()

        checks = [
            report["version"]["valid"],
            not report["missing_required_files"],
            report["dataset"]["valid"],
            report["benchmark"]["valid"],
            report["evaluations"]["valid"],
            report["compile"]["passed"],
        ]
        if run_tests:
            checks.append(report["tests"]["passed"])
        report["accepted"] = all(checks)
        report["acceptance_sha256"] = stable_sha256(report)
        return report
