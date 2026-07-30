from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.baselines import generate_baseline_responses
from core.cases import generate_cases
from core.prompts import generate_prompts
from core.scoring import score_responses
from plugins.left_twin import LeftTwinPlugin, is_prime_64


class LeftTwinV11Tests(unittest.TestCase):
    def test_primality_and_structural_validity(self) -> None:
        self.assertTrue(is_prime_64(3))
        self.assertTrue(is_prime_64(5))
        self.assertTrue(is_prime_64(59))
        self.assertFalse(is_prime_64(9))

    def test_synthetic_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            prime_root = project / "repository" / "ranges"
            gap_root = project / "repository" / "gaps_u16"
            experiment_root = project / "experiments" / "EXP-000002"
            prime_root.mkdir(parents=True)
            gap_root.mkdir(parents=True)

            primes = np.asarray(
                [3, 5, 7, 11, 13, 17, 19, 23, 29, 31,
                 37, 41, 43, 47, 53, 59, 61, 67, 71, 73,
                 79, 83, 89, 97, 101, 103, 107, 109],
                dtype=np.uint64,
            )
            gaps = np.asarray(
                [2, 2, 4, 2, 4, 2, 4, 6, 2, 6,
                 4, 2, 4, 6, 6, 2, 6, 4, 2, 6,
                 4, 6, 8, 4, 2, 4, 2, 0],
                dtype=np.uint16,
            )
            np.save(prime_root / "primes_1_200.npy", primes)
            np.save(gap_root / "gaps_1_200.npy", gaps)

            config = {
                "experiment": {
                    "id": "EXP-000002",
                    "name": "Synthetic Left Twin",
                    "version": "1.1.0",
                },
                "paths": {
                    "experiment_root": str(experiment_root),
                },
                "repository": {
                    "prime_root": str(prime_root),
                    "gap_root": str(gap_root),
                },
                "sequence": {
                    "plugin": "left_twin",
                    "dataset_file": "data/left_twin_primes.u64.npy",
                    "metadata_file": "data/left_twin_primes.metadata.json",
                    "target_count": 11,
                },
                "sampling": {
                    "endpoints": [10],
                    "window_sizes": [4],
                    "representations": ["absolute", "gaps", "combined"],
                    "definition_conditions": ["hidden", "disclosed"],
                },
                "prompt": {"target_label": "left twin prime"},
            }

            plugin = LeftTwinPlugin(config)
            source = plugin.validate_source()
            self.assertTrue(source["sufficient"])

            dataset = plugin.build_dataset()
            validation = plugin.validate_dataset(dataset)
            self.assertEqual(validation["count"], 11)
            self.assertEqual(validation["held_out_target_value"], 107)

            cases = generate_cases(config, plugin)
            self.assertEqual(len(cases), 6)
            self.assertEqual(generate_prompts(config, plugin), 6)

            counts = generate_baseline_responses(config, plugin)
            self.assertTrue(counts)

            score_path = score_responses(config, plugin)
            self.assertTrue(score_path.exists())

            metadata = json.loads(
                (experiment_root / "data" / "left_twin_primes.metadata.json")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["plugin_version"], "1.1.0")


if __name__ == "__main__":
    unittest.main()
