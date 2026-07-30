from __future__ import annotations
import tempfile,unittest
from pathlib import Path
import numpy as np
from sequence_plugins.builtin.prime_value import PrimeValueSequencePlugin
from sequence_plugins.loader import PluginRegistry
ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'registries'/'sequence_plugin_registry.csv'

def config(root:Path,count:int)->dict:
    return {'_experiment_root':str(root.parent),'repository':{'prime_root':str(root),'read_only':True},'sequence':{'target_count':count},'validation':{'full_partition_monotonic_check':True}}

class PrimeValuePhaseATests(unittest.TestCase):
    def test_registry_loads_plugin(self):
        p=PluginRegistry.from_path(REGISTRY).create('prime_value')
        self.assertIsInstance(p,PrimeValueSequencePlugin); self.assertEqual(p.plugin_version,'1.3.0')
    def test_structural_validity(self):
        p=PrimeValueSequencePlugin(); self.assertTrue(p.is_structurally_valid(2)); self.assertTrue(p.is_structurally_valid(101)); self.assertFalse(p.is_structurally_valid(105)); self.assertFalse(p.is_structurally_valid(True))
    def test_numeric_order_and_validation(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t)/'ranges'; r.mkdir()
            np.save(r/'primes_11_20.npy',np.array([11,13,17,19],dtype=np.uint64))
            np.save(r/'primes_1_10.npy',np.array([2,3,5,7],dtype=np.uint64))
            result=PrimeValueSequencePlugin(config(r,8)).validate_source(r)
            self.assertEqual(result['first_partition'],'primes_1_10.npy'); self.assertEqual(result['available_prime_count'],8); self.assertTrue(result['sufficient'])
    def test_insufficient_source(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t)/'ranges'; r.mkdir(); np.save(r/'primes_1_10.npy',np.array([2,3,5,7],dtype=np.uint64))
            self.assertFalse(PrimeValueSequencePlugin(config(r,5)).validate_source(r)['sufficient'])
    def test_partition_gap_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t)/'ranges'; r.mkdir(); np.save(r/'primes_1_10.npy',np.array([2,3,5,7],dtype=np.uint64)); np.save(r/'primes_12_20.npy',np.array([13,17,19],dtype=np.uint64))
            with self.assertRaisesRegex(ValueError,'adjacency failure'): PrimeValueSequencePlugin(config(r,7)).validate_source(r)
    def test_wrong_dtype_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t)/'ranges'; r.mkdir(); np.save(r/'primes_1_10.npy',np.array([2,3,5,7],dtype=np.int64))
            with self.assertRaisesRegex(ValueError,'unsigned integer dtype'): PrimeValueSequencePlugin(config(r,4)).validate_source(r)
    def test_phase_b_requires_valid_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prime_root = root / "ranges"
            prime_root.mkdir()

            destination = root / "prime_values.npy"

            plugin = PrimeValueSequencePlugin(
                {
                    "_experiment_root": str(root),
                    "repository": {
                        "prime_root": str(prime_root),
                        "read_only": True,
                    },
                    "sequence": {
                        "representation": "absolute",
                        "target_count": 1,
                    },
                    "validation": {
                        "full_partition_monotonic_check": True,
                    },
                }
            )

            with self.assertRaisesRegex(
                ValueError,
                "No canonical partitions found",
            ):
                plugin.build_dataset(
                    prime_root,
                    destination,
                    count=1,
                )

            self.assertFalse(destination.exists())

            metadata = destination.with_suffix(
                ".metadata.json"
            )
            self.assertFalse(metadata.exists())

