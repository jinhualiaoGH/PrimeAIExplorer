from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from plugins.left_twin import LeftTwinPlugin
from sequence_plugins.loader import PluginRegistry
from sequence_plugins.builtin.integer_sequence import IntegerSequencePlugin
from sequence_plugins.builtin.left_twin import LeftTwinSequencePlugin


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registries" / "sequence_plugin_registry.csv"


class SequenceFrameworkV121Tests(unittest.TestCase):
    def test_builtin_package_does_not_eagerly_import_plugins(self) -> None:
        import sequence_plugins.builtin as builtin

        self.assertIn("left_twin", builtin.__all__)

    def test_registry_loads_left_twin_adapter(self) -> None:
        registry = PluginRegistry.from_path(REGISTRY)
        plugin = registry.create("left_twin")
        self.assertIsInstance(plugin, LeftTwinSequencePlugin)

    def test_adapter_uses_verified_legacy_class(self) -> None:
        self.assertTrue(callable(LeftTwinPlugin.validate_source))
        self.assertTrue(callable(LeftTwinPlugin.build_dataset))
        self.assertTrue(callable(LeftTwinPlugin.make_window))

    def test_adapter_structural_validity(self) -> None:
        plugin = LeftTwinSequencePlugin()
        self.assertTrue(plugin.is_structurally_valid(3))
        self.assertTrue(plugin.is_structurally_valid(5))
        self.assertTrue(plugin.is_structurally_valid(101))
        self.assertFalse(plugin.is_structurally_valid(103))

    def test_adapter_requires_configuration_for_repository_work(self) -> None:
        plugin = LeftTwinSequencePlugin()
        with self.assertRaisesRegex(ValueError, "complete EXP-000002"):
            plugin.validate_source(Path("."))

    def test_adapter_delegates_source_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prime_root = root / "primes"
            gap_root = root / "gaps"
            data_root = root / "data"
            prime_root.mkdir()
            gap_root.mkdir()
            data_root.mkdir()

            primes = np.array(
                [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 41],
                dtype=np.uint64,
            )
            gaps = np.array(
                [1, 2, 2, 4, 2, 4, 2, 4, 6, 2, 10, 2],
                dtype=np.uint16,
            )
            np.save(prime_root / "primes_1_100.npy", primes)
            np.save(gap_root / "gaps_1_100.npy", gaps)

            config = {
                "_experiment_root": str(root),
                "experiment": {"id": "EXP-TEST", "version": "1.2.1"},
                "repository": {
                    "prime_root": str(prime_root),
                    "gap_root": str(gap_root),
                },
                "sequence": {
                    "target_count": 8,
                    "dataset_file": "data/left_twins.npy",
                    "metadata_file": "data/left_twins.metadata.json",
                },
            }
            plugin = LeftTwinSequencePlugin(config)
            result = plugin.validate_source(Path(root), required_count=8)
            self.assertEqual(result["left_twin_count"], 8)
            self.assertTrue(result["sufficient"])


if __name__ == "__main__":
    unittest.main()
