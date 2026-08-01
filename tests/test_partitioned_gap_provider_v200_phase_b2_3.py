from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

import numpy as np

from execution import ExecutionEngine
from kernel import ConfigurationError, ExecutionContext, ValidationError
from plugin_runtime import ManifestRegistry, PluginExecutionPipeline, PluginManifest
from runtime import RuntimeConfiguration, RuntimeSession
from sequence_api import (
    GapRepositoryManifest,
    PartitionedGapSequenceProvider,
    SequenceExecutionPlugin,
    SequenceProvider,
    SequenceWindowRequest,
    file_sha256,
)


class PartitionedGapProviderTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="b23-gap-test",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b2.3",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B23-TEST",
            created_utc="2026-08-01T01:00:00.000000Z",
        )
        session = RuntimeSession(
            context=context,
            configuration=RuntimeConfiguration.empty(),
        )
        session.initialize()
        session.start()
        return session

    def create_repository(
        self,
        root: Path,
        partitions=((2, 4, 2), (6, 6, 8), (4, 2, 10)),
        *,
        dtype=np.uint16,
        index_origin=1,
        include_hashes=True,
    ) -> Path:
        entries = []
        cursor = index_origin
        for ordinal, values in enumerate(partitions):
            path = root / f"gaps_{ordinal:03d}.npy"
            np.save(path, np.asarray(values, dtype=dtype))
            entry = {
                "ordinal": ordinal,
                "start_index": cursor,
                "count": len(values),
                "path": path.name,
            }
            if include_hashes:
                entry["sha256"] = file_sha256(path)
            entries.append(entry)
            cursor += len(values)
        manifest = {
            "schema_version": "1.0",
            "repository_id": "test-gap-repository",
            "repository_version": "1.0.0",
            "dtype": "uint16",
            "index_origin": index_origin,
            "partitions": entries,
            "metadata": {"ownership": "one index owns one outgoing gap"},
        }
        path = root / "gap_manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return path

    def test_provider_implements_protocol(self):
        provider = PartitionedGapSequenceProvider("gap", "manifest.json")
        self.assertIsInstance(provider, SequenceProvider)
        provider.close()

    def test_manifest_load(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.create_repository(root)
            manifest = GapRepositoryManifest.load(path)
            self.assertEqual(manifest.length, 9)
            self.assertEqual(manifest.end_index, 9)

    def test_missing_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "missing.json") as provider:
                with self.assertRaises(ConfigurationError):
                    provider.describe(session.context)

    def test_noncontiguous_partitions_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.create_repository(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["partitions"][1]["start_index"] += 1
            path.write_text(json.dumps(payload), encoding="utf-8")
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", path.name) as provider:
                with self.assertRaises(ValidationError):
                    provider.describe(session.context)

    def test_descriptor_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "gap_manifest.json") as provider:
                descriptor = provider.describe(session.context)
                self.assertEqual(descriptor.length, 9)
                self.assertEqual(descriptor.index_origin, 1)
                self.assertEqual(descriptor.value_type.value, "integer")
                self.assertEqual(descriptor.metadata["repository_dtype"], "uint16")
                self.assertEqual(descriptor.metadata["partition_count"], 3)

    def test_single_partition_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "gap_manifest.json") as provider:
                window = provider.read_window(
                    SequenceWindowRequest("gap", 2, 2), session.context
                )
                self.assertEqual(window.values, (4, 2))

    def test_cross_partition_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "gap_manifest.json") as provider:
                window = provider.read_window(
                    SequenceWindowRequest("gap", 3, 5), session.context
                )
                self.assertEqual(window.values, (2, 6, 6, 8, 4))

    def test_complete_repository_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "gap_manifest.json") as provider:
                window = provider.read_window(
                    SequenceWindowRequest("gap", 1, 9), session.context
                )
                self.assertEqual(
                    window.values, (2, 4, 2, 6, 6, 8, 4, 2, 10)
                )

    def test_before_origin_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "gap_manifest.json") as provider:
                with self.assertRaises(ValidationError):
                    provider.read_window(
                        SequenceWindowRequest("gap", 0, 1), session.context
                    )

    def test_overrun_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "gap_manifest.json") as provider:
                with self.assertRaises(ValidationError):
                    provider.read_window(
                        SequenceWindowRequest("gap", 9, 2), session.context
                    )

    def test_wrong_sequence_id_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "gap_manifest.json") as provider:
                with self.assertRaises(ValidationError):
                    provider.read_window(
                        SequenceWindowRequest("other", 1, 1), session.context
                    )

    def test_wrong_dtype_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root, dtype=np.uint32)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", "gap_manifest.json") as provider:
                with self.assertRaises(ValidationError):
                    provider.read_window(
                        SequenceWindowRequest("gap", 1, 1), session.context
                    )

    def test_partition_count_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.create_repository(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["partitions"][0]["count"] += 1
            payload["partitions"][1]["start_index"] += 1
            path.write_text(json.dumps(payload), encoding="utf-8")
            session = self.make_session(root)
            with PartitionedGapSequenceProvider("gap", path.name) as provider:
                with self.assertRaises(ValidationError):
                    provider.read_window(
                        SequenceWindowRequest("gap", 1, 1), session.context
                    )

    def test_partition_sha256_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider(
                "gap", "gap_manifest.json", verify_partition_sha256=True
            ) as provider:
                self.assertEqual(
                    provider.read_window(
                        SequenceWindowRequest("gap", 1, 2), session.context
                    ).values,
                    (2, 4),
                )

    def test_partition_sha256_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.create_repository(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["partitions"][0]["sha256"] = "0" * 64
            path.write_text(json.dumps(payload), encoding="utf-8")
            session = self.make_session(root)
            with PartitionedGapSequenceProvider(
                "gap", path.name, verify_partition_sha256=True
            ) as provider:
                with self.assertRaises(ValidationError):
                    provider.read_window(
                        SequenceWindowRequest("gap", 1, 1), session.context
                    )

    def test_cache_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with PartitionedGapSequenceProvider(
                "gap", "gap_manifest.json", cache_size=1
            ) as provider:
                provider.read_window(
                    SequenceWindowRequest("gap", 1, 9), session.context
                )
                self.assertLessEqual(provider.open_partition_count, 1)

    def test_close_releases_all_partitions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            provider = PartitionedGapSequenceProvider(
                "gap", "gap_manifest.json", cache_size=3
            )
            provider.read_window(
                SequenceWindowRequest("gap", 1, 9), session.context
            )
            self.assertEqual(provider.open_partition_count, 3)
            provider.close()
            self.assertEqual(provider.open_partition_count, 0)

    def test_descriptor_hash_stable(self):
        hashes = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.create_repository(root)
                session = self.make_session(root)
                with PartitionedGapSequenceProvider(
                    "gap", "gap_manifest.json"
                ) as provider:
                    hashes.append(provider.describe(session.context).descriptor_sha256)
        self.assertEqual(hashes[0], hashes[1])

    def test_adapter_constructs_gap_provider(self):
        plugin = SequenceExecutionPlugin(
            configuration={
                "providers": [{
                    "provider_type": "partitioned_gap_uint16",
                    "sequence_id": "gap",
                    "manifest_path": "gap_manifest.json",
                }]
            }
        )
        try:
            self.assertIsInstance(
                plugin.registry.resolve("gap"),
                PartitionedGapSequenceProvider,
            )
        finally:
            plugin.close()

    def test_pipeline_cross_partition_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(
                PluginManifest(
                    schema_version="1.0",
                    plugin_id="sequence_api",
                    plugin_version="2.0.0-phase-b2.3",
                    module="sequence_api.adapter",
                    class_name="SequenceExecutionPlugin",
                    capabilities=("sequence.window",),
                    enabled=True,
                    configuration={
                        "providers": [{
                            "provider_type": "partitioned_gap_uint16",
                            "sequence_id": "gap",
                            "manifest_path": "gap_manifest.json",
                        }]
                    },
                )
            )
            pipeline = PluginExecutionPipeline(engine, registry)
            try:
                record = pipeline.execute(
                    execution_id="EXEC-B23-GAP",
                    capability="sequence.window",
                    payload={
                        "operation": "window",
                        "sequence_id": "gap",
                        "start_index": 3,
                        "count": 5,
                    },
                )
                self.assertTrue(record.success)
                self.assertEqual(
                    engine.output("EXEC-B23-GAP")["values"],
                    [2, 6, 6, 8, 4],
                )
            finally:
                pipeline.close_plugin("sequence_api")


if __name__ == "__main__":
    unittest.main()
