from __future__ import annotations

from pathlib import Path
import csv
import tempfile
import unittest

import numpy as np

from execution import ExecutionEngine
from kernel import ConfigurationError, ExecutionContext, ValidationError
from plugin_runtime import ManifestRegistry, PluginExecutionPipeline, PluginManifest
from runtime import RuntimeConfiguration, RuntimeSession
from sequence_api import (
    PrimeNetGapRepositoryAdapter,
    SequenceExecutionPlugin,
    SequenceProvider,
    SequenceWindowRequest,
    detect_primenet_columns,
    file_sha256,
)


class PrimeNetRepositoryAdapterTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="b24-primenet-test",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b2.4",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B24-TEST",
            created_utc="2026-08-01T02:00:00.000000Z",
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
        *,
        headers=("partition_index", "start_index", "gap_count", "file_path", "sha256"),
        include_start=True,
        include_ordinal=True,
        include_hash=True,
    ) -> Path:
        gap_root = root / "gaps_u16_v3"
        gap_root.mkdir(parents=True)
        values = ((2, 4, 2), (6, 6, 8), (4, 2, 10))
        rows = []
        cursor = 1
        for ordinal, data in enumerate(values):
            path = gap_root / f"gaps_{ordinal:03d}.npy"
            np.save(path, np.asarray(data, dtype=np.uint16))
            row = {
                "partition_index": ordinal,
                "start_index": cursor,
                "gap_count": len(data),
                "file_path": str(path.relative_to(root)),
                "sha256": file_sha256(path),
            }
            rows.append(row)
            cursor += len(data)
        manifest = root / "gap_repository_u16_v3_manifest.csv"
        chosen = []
        for header in headers:
            if header == "start_index" and not include_start:
                continue
            if header == "partition_index" and not include_ordinal:
                continue
            if header == "sha256" and not include_hash:
                continue
            chosen.append(header)
        with manifest.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=chosen)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row[key] for key in chosen})
        return manifest

    def make_adapter(self, root: Path, **kwargs):
        return PrimeNetGapRepositoryAdapter(
            sequence_id="prime-gap",
            repository_root=".",
            manifest_path="gap_repository_u16_v3_manifest.csv",
            repository_id="primenet-gap-u16-v3",
            repository_version="3.0.0",
            **kwargs,
        )

    def test_provider_implements_protocol(self):
        provider = PrimeNetGapRepositoryAdapter(
            "gap", ".", "manifest.csv"
        )
        self.assertIsInstance(provider, SequenceProvider)
        provider.close()

    def test_column_auto_detection(self):
        mapping = detect_primenet_columns(
            ["partition_index", "start_index", "gap_count", "file_path", "sha256"]
        )
        self.assertEqual(mapping.path, "file_path")
        self.assertEqual(mapping.count, "gap_count")

    def test_missing_path_column_rejected(self):
        with self.assertRaises(ValidationError):
            detect_primenet_columns(["partition_index", "gap_count"])

    def test_missing_repository_root_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self.make_session(root)
            with PrimeNetGapRepositoryAdapter(
                "gap", "missing", "manifest.csv"
            ) as provider:
                with self.assertRaises(ConfigurationError):
                    provider.describe(session.context)

    def test_missing_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self.make_session(root)
            with PrimeNetGapRepositoryAdapter(
                "gap", ".", "missing.csv"
            ) as provider:
                with self.assertRaises(ConfigurationError):
                    provider.describe(session.context)

    def test_auto_detected_manifest_translation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with self.make_adapter(root) as provider:
                manifest = provider.translate_manifest(session.context)
                self.assertEqual(manifest.length, 9)
                self.assertEqual(len(manifest.partitions), 3)

    def test_inferred_start_indices(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root, include_start=False)
            session = self.make_session(root)
            with self.make_adapter(root) as provider:
                manifest = provider.translate_manifest(session.context)
                self.assertEqual(
                    tuple(item.start_index for item in manifest.partitions),
                    (1, 4, 7),
                )

    def test_inferred_ordinals(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root, include_ordinal=False)
            session = self.make_session(root)
            with self.make_adapter(root) as provider:
                manifest = provider.translate_manifest(session.context)
                self.assertEqual(
                    tuple(item.ordinal for item in manifest.partitions),
                    (0, 1, 2),
                )

    def test_custom_column_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gap_root = root / "gaps"
            gap_root.mkdir()
            path = gap_root / "part.npy"
            np.save(path, np.asarray([2, 4], dtype=np.uint16))
            with (root / "manifest.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["block_no", "rows", "name"])
                writer.writeheader()
                writer.writerow({"block_no": 0, "rows": 2, "name": "gaps/part.npy"})
            session = self.make_session(root)
            with PrimeNetGapRepositoryAdapter(
                "gap",
                ".",
                "manifest.csv",
                column_mapping={
                    "ordinal": "block_no",
                    "count": "rows",
                    "path": "name",
                },
            ) as provider:
                self.assertEqual(provider.describe(session.context).length, 2)

    def test_descriptor_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with self.make_adapter(root) as provider:
                descriptor = provider.describe(session.context)
                self.assertEqual(descriptor.length, 9)
                self.assertEqual(
                    descriptor.metadata["source_type"],
                    "primenet_gap_repository",
                )
                self.assertEqual(len(descriptor.metadata["adapter_sha256"]), 64)

    def test_cross_partition_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with self.make_adapter(root) as provider:
                window = provider.read_window(
                    SequenceWindowRequest("prime-gap", 3, 5),
                    session.context,
                )
                self.assertEqual(window.values, (2, 6, 6, 8, 4))

    def test_partition_sha256_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            with self.make_adapter(
                root, verify_partition_sha256=True
            ) as provider:
                self.assertEqual(
                    provider.read_window(
                        SequenceWindowRequest("prime-gap", 1, 2),
                        session.context,
                    ).values,
                    (2, 4),
                )

    def test_adapter_identity_stable(self):
        identities = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.create_repository(root)
                session = self.make_session(root)
                with self.make_adapter(root) as provider:
                    provider.describe(session.context)
                    identities.append(provider.adapter_sha256)
        self.assertNotEqual(identities[0], identities[1])

    def test_close_releases_mappings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.create_repository(root)
            session = self.make_session(root)
            provider = self.make_adapter(root, cache_size=3)
            provider.read_window(
                SequenceWindowRequest("prime-gap", 1, 9),
                session.context,
            )
            self.assertEqual(provider.open_partition_count, 3)
            provider.close()
            self.assertEqual(provider.open_partition_count, 0)

    def test_plugin_constructs_adapter(self):
        plugin = SequenceExecutionPlugin(
            configuration={
                "providers": [{
                    "provider_type": "primenet_gap_repository",
                    "sequence_id": "gap",
                    "repository_root": ".",
                    "manifest_path": "manifest.csv",
                }]
            }
        )
        try:
            self.assertIsInstance(
                plugin.registry.resolve("gap"),
                PrimeNetGapRepositoryAdapter,
            )
        finally:
            plugin.close()

    def test_pipeline_window(self):
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
                    plugin_version="2.0.0-phase-b2.4",
                    module="sequence_api.adapter",
                    class_name="SequenceExecutionPlugin",
                    capabilities=("sequence.window",),
                    enabled=True,
                    configuration={
                        "providers": [{
                            "provider_type": "primenet_gap_repository",
                            "sequence_id": "prime-gap",
                            "repository_root": ".",
                            "manifest_path": "gap_repository_u16_v3_manifest.csv",
                            "repository_id": "primenet-gap-u16-v3",
                            "repository_version": "3.0.0",
                        }]
                    },
                )
            )
            pipeline = PluginExecutionPipeline(engine, registry)
            try:
                record = pipeline.execute(
                    execution_id="EXEC-B24-GAP",
                    capability="sequence.window",
                    payload={
                        "operation": "window",
                        "sequence_id": "prime-gap",
                        "start_index": 3,
                        "count": 5,
                    },
                )
                self.assertTrue(record.success)
                self.assertEqual(
                    engine.output("EXEC-B24-GAP")["values"],
                    [2, 6, 6, 8, 4],
                )
            finally:
                pipeline.close_plugin("sequence_api")


if __name__ == "__main__":
    unittest.main()
