from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import os
import random
import tempfile

import numpy as np


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        temp_path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        temp_path.write_text(value, encoding="utf-8", newline="\n")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


@dataclass(frozen=True)
class CaseGenerationPlan:
    experiment_id: str
    dataset: Path
    dataset_sha256: str
    output_root: Path
    window_sizes: tuple[int, ...]
    case_count_per_window: int
    sampling_seed: int
    minimum_target_index_1_based: int
    maximum_target_index_1_based: int
    total_case_count: int
    would_replace_output: bool
    writes_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "dataset": str(self.dataset),
            "dataset_sha256": self.dataset_sha256,
            "output_root": str(self.output_root),
            "window_sizes": list(self.window_sizes),
            "case_count_per_window": self.case_count_per_window,
            "sampling_seed": self.sampling_seed,
            "minimum_target_index_1_based": self.minimum_target_index_1_based,
            "maximum_target_index_1_based": self.maximum_target_index_1_based,
            "total_case_count": self.total_case_count,
            "would_replace_output": self.would_replace_output,
            "writes_performed": self.writes_performed,
        }


class PrimeValueCaseEngine:
    schema_version = "1.0"
    engine_version = "1.3.0"

    def __init__(self, config: Mapping[str, Any], *, project_root: Path) -> None:
        self.config = dict(config)
        self.project_root = project_root.resolve()
        self.experiment = self.config["experiment"]
        self.cases = self.config["cases"]
        self.prompts = self.config["prompts"]
        self.sequence = self.config["sequence"]

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path.resolve() if path.is_absolute() else (self.project_root / path).resolve()

    @property
    def dataset_path(self) -> Path:
        return self._resolve(
            f"experiments/{self.experiment['id']}/{self.sequence['dataset_file']}"
        )

    @property
    def dataset_metadata_path(self) -> Path:
        return self._resolve(
            f"experiments/{self.experiment['id']}/{self.sequence['metadata_file']}"
        )

    @property
    def output_root(self) -> Path:
        configured = self.cases.get("output_root", "benchmark")
        return self._resolve(
            f"experiments/{self.experiment['id']}/{configured}"
        )

    def _load_dataset_metadata(self) -> dict[str, Any]:
        if not self.dataset_metadata_path.exists():
            raise FileNotFoundError(
                f"Dataset metadata does not exist: {self.dataset_metadata_path}"
            )
        return json.loads(
            self.dataset_metadata_path.read_text(encoding="utf-8")
        )

    def plan(self) -> CaseGenerationPlan:
        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Prime Value dataset does not exist: {self.dataset_path}"
            )

        metadata = self._load_dataset_metadata()
        actual_hash = file_sha256(self.dataset_path)
        expected_hash = metadata.get("dataset_sha256") or metadata.get("sha256")
        if expected_hash != actual_hash:
            raise ValueError("Dataset SHA-256 does not match metadata.")

        values = np.load(self.dataset_path, mmap_mode="r", allow_pickle=False)
        if values.ndim != 1:
            raise ValueError("Prime Value dataset must be one-dimensional.")

        windows = tuple(int(v) for v in self.cases["window_sizes"])
        if len(set(windows)) != len(windows):
            raise ValueError("Window sizes must be unique.")
        if any(v <= 0 for v in windows):
            raise ValueError("Window sizes must be positive.")

        minimum = int(self.cases["minimum_target_index_1_based"])
        configured_maximum = int(self.cases["maximum_target_index_1_based"])
        maximum = min(configured_maximum, int(len(values)))
        count = int(self.cases["case_count_per_window"])
        if count <= 0:
            raise ValueError("case_count_per_window must be positive.")
        if minimum <= max(windows):
            raise ValueError(
                "minimum target index must exceed the largest observation window."
            )
        if maximum < minimum:
            raise ValueError("No valid target index range is available.")
        if maximum - minimum + 1 < count:
            raise ValueError("Target range is too small for unique sampling.")

        return CaseGenerationPlan(
            experiment_id=self.experiment["id"],
            dataset=self.dataset_path,
            dataset_sha256=actual_hash,
            output_root=self.output_root,
            window_sizes=windows,
            case_count_per_window=count,
            sampling_seed=int(self.cases["sampling_seed"]),
            minimum_target_index_1_based=minimum,
            maximum_target_index_1_based=maximum,
            total_case_count=count * len(windows),
            would_replace_output=self.output_root.exists(),
        )

    @staticmethod
    def _sample_targets(
        minimum: int,
        maximum: int,
        count: int,
        seed: int,
        window: int,
    ) -> list[int]:
        rng = random.Random((seed << 16) ^ window)
        return sorted(rng.sample(range(minimum, maximum + 1), count))

    @staticmethod
    def _case_id(window: int, ordinal: int) -> str:
        return f"CASE-W{window:03d}-{ordinal:06d}"

    def _render_prompt(self, public_case: Mapping[str, Any]) -> str:
        values = " ".join(str(v) for v in public_case["observation"])
        return (
            "SYSTEM\n"
            "You are participating in a controlled numerical continuation experiment. "
            "Follow the response format exactly.\n\n"
            "USER\n"
            "You are given a sequence of consecutive integer values.\n\n"
            f"Observation window size: {public_case['window_size']}\n\n"
            "Observed values:\n"
            f"{values}\n\n"
            "Predict the next value.\n\n"
            "Return JSON only using this exact structure:\n\n"
            "{\n"
            '  "prediction": <integer>,\n'
            '  "confidence": <integer from 0 to 100>,\n'
            '  "explanation": "<brief explanation>"\n'
            "}\n"
        )

    def generate(self, *, overwrite: bool = False) -> dict[str, Any]:
        plan = self.plan()
        if plan.output_root.exists() and not overwrite:
            raise FileExistsError(
                f"Benchmark output already exists; explicit overwrite required: "
                f"{plan.output_root}"
            )

        values = np.load(plan.dataset, mmap_mode="r", allow_pickle=False)

        temporary_root = plan.output_root.with_name(
            f".{plan.output_root.name}.tmp"
        )
        if temporary_root.exists():
            import shutil
            shutil.rmtree(temporary_root)
        temporary_root.mkdir(parents=True)

        public_dir = temporary_root / "cases" / "public"
        private_dir = temporary_root / "cases" / "private"
        prompt_dir = temporary_root / "prompts" / "text"
        public_dir.mkdir(parents=True)
        private_dir.mkdir(parents=True)
        prompt_dir.mkdir(parents=True)

        manifest_cases: list[dict[str, Any]] = []

        try:
            for window in plan.window_sizes:
                targets = self._sample_targets(
                    plan.minimum_target_index_1_based,
                    plan.maximum_target_index_1_based,
                    plan.case_count_per_window,
                    plan.sampling_seed,
                    window,
                )
                for ordinal, target_index_1_based in enumerate(targets, start=1):
                    case_id = self._case_id(window, ordinal)
                    target_zero = target_index_1_based - 1
                    start_zero = target_zero - window

                    observation = [
                        int(v) for v in values[start_zero:target_zero]
                    ]
                    target = int(values[target_zero])

                    public_case = {
                        "schema_version": self.schema_version,
                        "case_id": case_id,
                        "experiment_id": plan.experiment_id,
                        "plugin_id": "prime_value",
                        "representation": "absolute",
                        "window_size": window,
                        "observation_start_index_1_based": start_zero + 1,
                        "observation_end_index_1_based": target_zero,
                        "target_index_1_based": target_index_1_based,
                        "observation": observation,
                        "dataset_sha256": plan.dataset_sha256,
                    }
                    public_case["case_sha256"] = stable_sha256(public_case)

                    private_case = {
                        **public_case,
                        "target": target,
                    }
                    private_case["answer_key_sha256"] = stable_sha256(private_case)

                    prompt = self._render_prompt(public_case)
                    prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()

                    atomic_write_json(public_dir / f"{case_id}.json", public_case)
                    atomic_write_json(private_dir / f"{case_id}.json", private_case)
                    atomic_write_text(prompt_dir / f"{case_id}.txt", prompt)

                    manifest_cases.append(
                        {
                            "case_id": case_id,
                            "window_size": window,
                            "target_index_1_based": target_index_1_based,
                            "public_case_sha256": public_case["case_sha256"],
                            "answer_key_sha256": private_case["answer_key_sha256"],
                            "prompt_sha256": prompt_hash,
                        }
                    )

            manifest = {
                "schema_version": self.schema_version,
                "engine_version": self.engine_version,
                "experiment_id": plan.experiment_id,
                "plugin_id": "prime_value",
                "dataset_sha256": plan.dataset_sha256,
                "sampling_seed": plan.sampling_seed,
                "window_sizes": list(plan.window_sizes),
                "case_count_per_window": plan.case_count_per_window,
                "total_case_count": len(manifest_cases),
                "sequence_name_disclosed": bool(
                    self.prompts.get("disclose_sequence_name", False)
                ),
                "cases": manifest_cases,
            }
            manifest["manifest_sha256"] = stable_sha256(manifest)
            atomic_write_json(temporary_root / "manifest.json", manifest)

            if plan.output_root.exists():
                import shutil
                shutil.rmtree(plan.output_root)
            os.replace(temporary_root, plan.output_root)
            return manifest
        except Exception:
            import shutil
            shutil.rmtree(temporary_root, ignore_errors=True)
            raise

    def validate(self) -> dict[str, Any]:
        plan = self.plan()
        root = plan.output_root
        manifest_path = root / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest does not exist: {manifest_path}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stored_manifest_hash = manifest.pop("manifest_sha256")
        if stable_sha256(manifest) != stored_manifest_hash:
            raise ValueError("Manifest SHA-256 mismatch.")
        manifest["manifest_sha256"] = stored_manifest_hash

        seen_ids: set[str] = set()
        target_by_window: dict[int, set[int]] = {}
        for item in manifest["cases"]:
            case_id = item["case_id"]
            if case_id in seen_ids:
                raise ValueError(f"Duplicate case ID: {case_id}")
            seen_ids.add(case_id)

            public_path = root / "cases" / "public" / f"{case_id}.json"
            private_path = root / "cases" / "private" / f"{case_id}.json"
            prompt_path = root / "prompts" / "text" / f"{case_id}.txt"
            for path in (public_path, private_path, prompt_path):
                if not path.exists():
                    raise FileNotFoundError(f"Missing benchmark artifact: {path}")

            public_case = json.loads(public_path.read_text(encoding="utf-8"))
            private_case = json.loads(private_path.read_text(encoding="utf-8"))
            prompt = prompt_path.read_text(encoding="utf-8")

            public_hash = public_case.pop("case_sha256")
            if stable_sha256(public_case) != public_hash:
                raise ValueError(f"Public case hash mismatch: {case_id}")
            public_case["case_sha256"] = public_hash

            private_hash = private_case.pop("answer_key_sha256")
            if stable_sha256(private_case) != private_hash:
                raise ValueError(f"Private case hash mismatch: {case_id}")
            private_case["answer_key_sha256"] = private_hash

            if "target" in public_case:
                raise ValueError(f"Target leaked into public case: {case_id}")
            target_text = str(private_case["target"])
            if target_text in prompt:
                raise ValueError(f"Target leaked into prompt: {case_id}")
            if "prime" in prompt.casefold():
                raise ValueError(f"Sequence identity leaked into prompt: {case_id}")
            if len(public_case["observation"]) != public_case["window_size"]:
                raise ValueError(f"Observation length mismatch: {case_id}")
            if (
                public_case["observation_end_index_1_based"] + 1
                != public_case["target_index_1_based"]
            ):
                raise ValueError(f"Index adjacency mismatch: {case_id}")

            window = int(public_case["window_size"])
            targets = target_by_window.setdefault(window, set())
            target_index = int(public_case["target_index_1_based"])
            if target_index in targets:
                raise ValueError(
                    f"Duplicate target index within W{window:03d}: {target_index}"
                )
            targets.add(target_index)

            if sha256(prompt.encode("utf-8")).hexdigest() != item["prompt_sha256"]:
                raise ValueError(f"Prompt hash mismatch: {case_id}")

        expected = plan.total_case_count
        if len(seen_ids) != expected:
            raise ValueError(
                f"Expected {expected} cases; found {len(seen_ids)}."
            )

        return {
            "experiment_id": plan.experiment_id,
            "total_case_count": len(seen_ids),
            "window_sizes": list(plan.window_sizes),
            "case_count_per_window": plan.case_count_per_window,
            "dataset_sha256": plan.dataset_sha256,
            "manifest_sha256": stored_manifest_hash,
            "target_leakage_detected": False,
            "sequence_identity_disclosed": False,
            "valid": True,
        }
