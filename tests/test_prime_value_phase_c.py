from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.prime_value_cases import (
    PrimeValueCaseEngine,
    file_sha256,
)


def make_project(root: Path) -> dict:
    experiment_root = root / "experiments" / "EXP-000003"
    data = experiment_root / "data"
    data.mkdir(parents=True)

    values = np.array(
        [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
         53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109,
         113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179,
         181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241,
         251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313],
        dtype=np.uint64,
    )
    dataset = data / "prime_values.npy"
    np.save(dataset, values)
    metadata = {
        "dataset_sha256": file_sha256(dataset),
        "count": len(values),
        "dtype": "uint64",
    }
    (data / "prime_values.metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    return {
        "experiment": {"id": "EXP-000003"},
        "sequence": {
            "dataset_file": "data/prime_values.npy",
            "metadata_file": "data/prime_values.metadata.json",
        },
        "cases": {
            "window_sizes": [4, 8],
            "case_count_per_window": 3,
            "sampling_seed": 130003,
            "minimum_target_index_1_based": 12,
            "maximum_target_index_1_based": len(values),
            "output_root": "benchmark",
        },
        "prompts": {
            "disclose_sequence_name": False,
            "response_format": "json_prediction_v1",
        },
    }


class PhaseCTests(unittest.TestCase):
    def test_plan_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueCaseEngine(make_project(root), project_root=root)
            plan = engine.plan()
            self.assertEqual(plan.total_case_count, 6)
            self.assertFalse(plan.output_root.exists())
            self.assertFalse(plan.writes_performed)

    def test_generation_and_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueCaseEngine(make_project(root), project_root=root)
            manifest = engine.generate()
            self.assertEqual(manifest["total_case_count"], 6)
            result = engine.validate()
            self.assertTrue(result["valid"])
            self.assertFalse(result["target_leakage_detected"])

    def test_deterministic_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            root1 = Path(first)
            root2 = Path(second)
            first_manifest = PrimeValueCaseEngine(
                make_project(root1), project_root=root1
            ).generate()
            second_manifest = PrimeValueCaseEngine(
                make_project(root2), project_root=root2
            ).generate()
            self.assertEqual(
                first_manifest["manifest_sha256"],
                second_manifest["manifest_sha256"],
            )

    def test_public_cases_hide_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueCaseEngine(make_project(root), project_root=root)
            engine.generate()
            public = next(
                (engine.output_root / "cases" / "public").glob("*.json")
            )
            payload = json.loads(public.read_text(encoding="utf-8"))
            self.assertNotIn("target", payload)

    def test_prompt_hides_sequence_identity_and_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueCaseEngine(make_project(root), project_root=root)
            engine.generate()
            private = next(
                (engine.output_root / "cases" / "private").glob("*.json")
            )
            payload = json.loads(private.read_text(encoding="utf-8"))
            prompt = (
                engine.output_root / "prompts" / "text" / f"{payload['case_id']}.txt"
            ).read_text(encoding="utf-8")
            self.assertNotIn(str(payload["target"]), prompt)
            self.assertNotIn("prime", prompt.casefold())

    def test_one_based_index_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueCaseEngine(make_project(root), project_root=root)
            engine.generate()
            public = next(
                (engine.output_root / "cases" / "public").glob("*.json")
            )
            payload = json.loads(public.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["observation_end_index_1_based"] + 1,
                payload["target_index_1_based"],
            )
            self.assertEqual(
                len(payload["observation"]),
                payload["window_size"],
            )

    def test_overwrite_protection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueCaseEngine(make_project(root), project_root=root)
            engine.generate()
            with self.assertRaises(FileExistsError):
                engine.generate()
            engine.generate(overwrite=True)

    def test_dataset_hash_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = make_project(root)
            metadata_path = (
                root / "experiments" / "EXP-000003" /
                "data" / "prime_values.metadata.json"
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["dataset_sha256"] = "0" * 64
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                PrimeValueCaseEngine(config, project_root=root).plan()


if __name__ == "__main__":
    unittest.main()
