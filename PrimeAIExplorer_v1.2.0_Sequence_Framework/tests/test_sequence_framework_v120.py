from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from sequence_plugins.base import CaseRecord
from sequence_plugins.loader import PluginRegistry
from sequence_plugins.builtin.integer_sequence import IntegerSequencePlugin
from sequence_plugins.builtin.prime_gap import PrimeGapSequencePlugin
from sequence_plugins.builtin.prime_square import PrimeSquareSequencePlugin


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registries" / "sequence_plugin_registry.csv"


class SequenceFrameworkTests(unittest.TestCase):
    def test_registry_loads_active_plugins(self) -> None:
        registry = PluginRegistry.from_path(REGISTRY)
        active = registry.identifiers(active_only=True)
        self.assertIn("left_twin", active)
        self.assertIn("prime_gap", active)
        self.assertIn("prime_square", active)

    def test_inactive_plugin_is_rejected(self) -> None:
        registry = PluginRegistry.from_path(REGISTRY)
        with self.assertRaises(ValueError):
            registry.create("prime_cube")

    def test_integer_case_generation(self) -> None:
        plugin = IntegerSequencePlugin()
        values = [2, 3, 5, 7, 11, 13]
        cases = plugin.generate_cases(
            values,
            endpoints=[4, 5],
            window_size=3,
            representation="absolute",
            experiment_id="EXP-TEST",
        )
        self.assertEqual(len(cases), 2)
        self.assertEqual(cases[0].observation, (3, 5, 7))
        self.assertEqual(cases[0].target, 11)

    def test_gap_representation(self) -> None:
        plugin = IntegerSequencePlugin()
        cases = plugin.generate_cases(
            [3, 5, 11, 17, 29],
            endpoints=[4],
            window_size=4,
            representation="gaps",
            experiment_id="EXP-TEST",
        )
        self.assertEqual(cases[0].observation, (2, 6, 6))
        self.assertEqual(cases[0].target, 12)

    def test_prompt_hides_definition_by_default(self) -> None:
        plugin = IntegerSequencePlugin()
        case = CaseRecord(
            case_id="CASE-1",
            plugin_id=plugin.plugin_id,
            representation="absolute",
            observation=(1, 2, 3),
            target=4,
            metadata={},
        )
        prompt = plugin.render_prompt(case)
        self.assertNotIn(plugin.display_name, prompt)
        disclosed = plugin.render_prompt(case, disclose_definition=True)
        self.assertIn(plugin.display_name, disclosed)

    def test_prime_gap_structural_validity(self) -> None:
        plugin = PrimeGapSequencePlugin()
        self.assertTrue(plugin.is_structurally_valid(6))
        self.assertFalse(plugin.is_structurally_valid(7))
        self.assertFalse(plugin.is_structurally_valid(0))

    def test_prime_square_dataset(self) -> None:
        plugin = PrimeSquareSequencePlugin()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "primes.npy"
            destination = root / "prime_squares.npy"
            np.save(source, np.array([2, 3, 5, 7, 11], dtype=np.uint64))

            metadata = plugin.build_dataset(
                source,
                destination,
                count=5,
            )
            values = np.load(destination)
            self.assertEqual(values.tolist(), [4, 9, 25, 49, 121])
            self.assertEqual(metadata.count, 5)
            self.assertTrue(plugin.is_structurally_valid(121))
            self.assertFalse(plugin.is_structurally_valid(120))

    def test_prediction_evaluation(self) -> None:
        plugin = PrimeGapSequencePlugin()
        result = plugin.evaluate_prediction("6", 6)
        self.assertTrue(result.exact)
        self.assertTrue(result.structurally_valid)
        invalid = plugin.evaluate_prediction("7", 6)
        self.assertFalse(invalid.exact)
        self.assertFalse(invalid.structurally_valid)


if __name__ == "__main__":
    unittest.main()
