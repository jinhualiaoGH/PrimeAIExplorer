from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

import numpy as np

from execution import ExecutionEngine
from kernel import ConfigurationError, ExecutionContext, ValidationError
from plugin_runtime import ManifestRegistry, PluginExecutionPipeline, PluginManifest
from runtime import RuntimeConfiguration, RuntimeSession
from sequence_api import (
    NpyMemmapSequenceProvider,
    SequenceExecutionPlugin,
    SequenceProvider,
    SequenceWindowRequest,
    file_sha256,
)


class MemmapSequenceProviderTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="memmap-provider-test",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b2.2-r3",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B22-R3-TEST",
            created_utc="2026-08-01T00:00:00.000000Z",
        )
        session = RuntimeSession(
            context=context,
            configuration=RuntimeConfiguration.empty(),
        )
        session.initialize()
        session.start()
        return session

    @staticmethod
    def save(root: Path, values, name: str = "values.npy") -> Path:
        path = root / name
        np.save(path, np.asarray(values))
        return path

    @contextmanager
    def mapped_provider(
        self,
        values,
        *,
        sequence_id: str = "prime",
        source_path: str = "values.npy",
        provider_kwargs: dict | None = None,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.save(root, values)
            session = self.make_session(root)
            provider = NpyMemmapSequenceProvider(
                sequence_id,
                source_path,
                **(provider_kwargs or {}),
            )
            try:
                yield root, path, session, provider
            finally:
                provider.close()

    def test_file_sha256_matches_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "data.bin"
            path.write_bytes(b"PrimeAIExplorer")
            self.assertEqual(
                file_sha256(path),
                sha256(b"PrimeAIExplorer").hexdigest(),
            )

    def test_provider_implements_protocol(self):
        provider = NpyMemmapSequenceProvider("x", "x.npy")
        self.assertIsInstance(provider, SequenceProvider)
        provider.close()

    def test_relative_path_resolves_from_project_root(self):
        with self.mapped_provider([2, 3, 5]) as (_, _, session, provider):
            self.assertEqual(provider.describe(session.context).length, 3)

    def test_absolute_path_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.save(root, [2, 3, 5])
            session = self.make_session(root)
            with NpyMemmapSequenceProvider("prime", str(path)) as provider:
                self.assertEqual(provider.describe(session.context).length, 3)

    def test_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self.make_session(root)
            with NpyMemmapSequenceProvider("x", "missing.npy") as provider:
                with self.assertRaises(ConfigurationError):
                    provider.describe(session.context)

    def test_non_npy_file_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "x.bin").write_bytes(b"123")
            session = self.make_session(root)
            with NpyMemmapSequenceProvider("x", "x.bin") as provider:
                with self.assertRaises(ConfigurationError):
                    provider.describe(session.context)

    def test_two_dimensional_array_rejected(self):
        with self.mapped_provider([[1, 2], [3, 4]], sequence_id="x") as (_, _, session, provider):
            with self.assertRaises(ValidationError):
                provider.describe(session.context)

    def test_empty_array_rejected(self):
        with self.mapped_provider(np.array([], dtype=np.int64), sequence_id="x") as (_, _, session, provider):
            with self.assertRaises(ValidationError):
                provider.describe(session.context)

    def test_boolean_dtype_rejected(self):
        with self.mapped_provider([True, False], sequence_id="x") as (_, _, session, provider):
            with self.assertRaises(ValidationError):
                provider.describe(session.context)

    def test_integer_descriptor_contract(self):
        with self.mapped_provider(
            np.array([2, 3, 5], dtype=np.uint64),
            provider_kwargs={"index_origin": 1, "strictly_increasing": True},
        ) as (_, _, session, provider):
            descriptor = provider.describe(session.context)
            self.assertEqual(descriptor.value_type.value, "integer")
            self.assertEqual(descriptor.index_origin, 1)
            self.assertTrue(descriptor.metadata["read_only"])
            self.assertTrue(descriptor.metadata["memory_mapped"])

    def test_real_descriptor_contract(self):
        with self.mapped_provider(
            np.array([1.25, 2.5], dtype=np.float64),
            sequence_id="real",
        ) as (_, _, session, provider):
            self.assertEqual(
                provider.describe(session.context).value_type.value,
                "real",
            )

    def test_identity_contains_file_sha256(self):
        with self.mapped_provider([2, 3, 5]) as (_, path, session, provider):
            provider.describe(session.context)
            self.assertEqual(provider.identity.file_sha256, file_sha256(path))

    def test_expected_sha256_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.save(root, [2, 3, 5])
            session = self.make_session(root)
            with NpyMemmapSequenceProvider(
                "prime",
                "values.npy",
                expected_sha256=file_sha256(path),
            ) as provider:
                self.assertEqual(provider.describe(session.context).length, 3)

    def test_expected_sha256_mismatch_rejected(self):
        with self.mapped_provider(
            [2, 3, 5],
            provider_kwargs={"expected_sha256": "0" * 64},
        ) as (_, _, session, provider):
            with self.assertRaises(ValidationError):
                provider.describe(session.context)

    def test_mapping_is_read_only(self):
        with self.mapped_provider([2, 3, 5]) as (_, _, session, provider):
            provider.describe(session.context)
            self.assertFalse(provider._array.flags.writeable)
            with self.assertRaises(ValueError):
                provider._array[0] = 9

    def test_mapping_is_lazy(self):
        provider = NpyMemmapSequenceProvider("x", "x.npy")
        self.assertFalse(provider.is_open)
        provider.close()

    def test_mapping_reused_between_reads(self):
        with self.mapped_provider([2, 3, 5, 7]) as (_, _, session, provider):
            provider.describe(session.context)
            original = provider._array
            provider.read_window(
                SequenceWindowRequest("prime", 0, 2),
                session.context,
            )
            self.assertIs(provider._array, original)

    def test_close_releases_provider_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.save(root, [2, 3, 5])
            session = self.make_session(root)
            provider = NpyMemmapSequenceProvider("prime", "values.npy")
            provider.describe(session.context)
            provider.close()
            self.assertFalse(provider.is_open)
            with self.assertRaises(ConfigurationError):
                _ = provider.identity

    def test_context_manager_releases_provider_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.save(root, [2, 3, 5])
            session = self.make_session(root)
            provider = NpyMemmapSequenceProvider("prime", "values.npy")
            with provider:
                provider.describe(session.context)
                self.assertTrue(provider.is_open)
            self.assertFalse(provider.is_open)

    def test_exact_boundary_window(self):
        with self.mapped_provider(
            [2, 3, 5, 7, 11],
            provider_kwargs={"index_origin": 1},
        ) as (_, _, session, provider):
            window = provider.read_window(
                SequenceWindowRequest("prime", 3, 3),
                session.context,
            )
            self.assertEqual(window.values, (5, 7, 11))
            self.assertEqual(window.end_index, 5)

    def test_before_origin_rejected(self):
        with self.mapped_provider(
            [2, 3, 5],
            provider_kwargs={"index_origin": 1},
        ) as (_, _, session, provider):
            with self.assertRaises(ValidationError):
                provider.read_window(
                    SequenceWindowRequest("prime", 0, 1),
                    session.context,
                )

    def test_boundary_overrun_rejected(self):
        with self.mapped_provider([2, 3, 5]) as (_, _, session, provider):
            with self.assertRaises(ValidationError):
                provider.read_window(
                    SequenceWindowRequest("prime", 2, 2),
                    session.context,
                )

    def test_integer_scalars_become_python_ints(self):
        with self.mapped_provider(
            np.array([2, 3], dtype=np.uint64)
        ) as (_, _, session, provider):
            window = provider.read_window(
                SequenceWindowRequest("prime", 0, 2),
                session.context,
            )
            self.assertTrue(all(type(value) is int for value in window.values))

    def test_float_scalars_become_python_floats(self):
        with self.mapped_provider(
            np.array([1.5, 2.5], dtype=np.float64),
            sequence_id="real",
        ) as (_, _, session, provider):
            window = provider.read_window(
                SequenceWindowRequest("real", 0, 2),
                session.context,
            )
            self.assertTrue(all(type(value) is float for value in window.values))

    def test_descriptor_hash_path_independent(self):
        descriptors = []
        for name in ("one", "two"):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / name
                root.mkdir()
                self.save(root, [2, 3, 5])
                session = self.make_session(root)
                with NpyMemmapSequenceProvider("prime", "values.npy") as provider:
                    descriptors.append(
                        provider.describe(session.context).descriptor_sha256
                    )
        self.assertEqual(descriptors[0], descriptors[1])

    def test_adapter_constructs_memmap_provider(self):
        plugin = SequenceExecutionPlugin(
            configuration={
                "providers": [{
                    "provider_type": "numpy_npy_memmap",
                    "sequence_id": "prime",
                    "source_path": "values.npy",
                }]
            }
        )
        try:
            self.assertIsInstance(
                plugin.registry.resolve("prime"),
                NpyMemmapSequenceProvider,
            )
        finally:
            plugin.close()

    def test_adapter_rejects_unknown_provider_type(self):
        with self.assertRaises(ValidationError):
            SequenceExecutionPlugin(
                configuration={
                    "providers": [{
                        "provider_type": "unknown",
                        "sequence_id": "x",
                    }]
                }
            )

    def test_pipeline_memmap_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.save(root, np.array([2, 3, 5, 7, 11], dtype=np.uint64))
            session = self.make_session(root)
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(
                PluginManifest(
                    schema_version="1.0",
                    plugin_id="sequence_api",
                    plugin_version="2.0.0-phase-b2.2-r3",
                    module="sequence_api.adapter",
                    class_name="SequenceExecutionPlugin",
                    capabilities=("sequence.window",),
                    enabled=True,
                    configuration={
                        "providers": [{
                            "provider_type": "numpy_npy_memmap",
                            "sequence_id": "prime",
                            "source_path": "values.npy",
                            "index_origin": 1,
                        }]
                    },
                )
            )
            pipeline = PluginExecutionPipeline(engine, registry)
            try:
                record = pipeline.execute(
                    execution_id="EXEC-B22-R3-WINDOW",
                    capability="sequence.window",
                    payload={
                        "operation": "window",
                        "sequence_id": "prime",
                        "start_index": 2,
                        "count": 3,
                    },
                )
                self.assertTrue(record.success)
                self.assertEqual(
                    engine.output("EXEC-B22-R3-WINDOW")["values"],
                    [3, 5, 7],
                )
            finally:
                pipeline.close_plugin("sequence_api")

    def test_plugin_close_closes_memmap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.save(root, [2, 3, 5])
            session = self.make_session(root)
            plugin = SequenceExecutionPlugin(
                configuration={
                    "providers": [{
                        "provider_type": "numpy_npy_memmap",
                        "sequence_id": "prime",
                        "source_path": "values.npy",
                    }]
                }
            )
            provider = plugin.registry.resolve("prime")
            plugin.execute(
                {"operation": "describe", "sequence_id": "prime"},
                session.context,
            )
            self.assertTrue(provider.is_open)
            plugin.close()
            self.assertFalse(provider.is_open)


if __name__ == "__main__":
    unittest.main()
