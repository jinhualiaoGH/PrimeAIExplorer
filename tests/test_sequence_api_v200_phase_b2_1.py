from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from execution import ExecutionEngine
from kernel import (
    ConfigurationError,
    ExecutionContext,
    ValidationError,
)
from plugin_runtime import (
    ManifestRegistry,
    PluginExecutionPipeline,
    PluginManifest,
)
from runtime import RuntimeConfiguration, RuntimeSession
from sequence_api import (
    InMemorySequenceProvider,
    SequenceBatch,
    SequenceBatchRequest,
    SequenceDescriptor,
    SequenceExecutionPlugin,
    SequenceProvider,
    SequenceProviderRegistry,
    SequenceValueType,
    SequenceWindow,
    SequenceWindowRequest,
)


class SequenceApiTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="sequence-api-test",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b2.1",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B21-TEST",
            created_utc="2026-07-31T23:00:00.000000Z",
        )
        session = RuntimeSession(
            context=context,
            configuration=RuntimeConfiguration.empty(),
        )
        session.initialize()
        session.start()
        return session

    def descriptor(self):
        return SequenceDescriptor(
            schema_version="1.0",
            sequence_id="prime-value",
            sequence_version="1.0.0",
            title="Prime values",
            value_type=SequenceValueType.INTEGER,
            index_origin=1,
            finite=True,
            length=5,
            strictly_increasing=True,
            metadata={},
        )

    def test_descriptor_hash_stable(self):
        self.assertEqual(
            self.descriptor().descriptor_sha256,
            self.descriptor().descriptor_sha256,
        )

    def test_finite_descriptor_requires_length(self):
        with self.assertRaises(ValidationError):
            SequenceDescriptor(
                "1.0", "x", "1", "X",
                SequenceValueType.INTEGER,
                0, True, None, False, {},
            )

    def test_infinite_descriptor_rejects_length(self):
        with self.assertRaises(ValidationError):
            SequenceDescriptor(
                "1.0", "x", "1", "X",
                SequenceValueType.INTEGER,
                0, False, 10, False, {},
            )

    def test_window_request_hash_stable(self):
        request = SequenceWindowRequest("x", 0, 3)
        self.assertEqual(
            request.request_sha256,
            SequenceWindowRequest("x", 0, 3).request_sha256,
        )

    def test_window_request_rejects_zero_count(self):
        with self.assertRaises(ValidationError):
            SequenceWindowRequest("x", 0, 0)

    def test_window_calculates_end_index(self):
        window = SequenceWindow(
            self.descriptor().descriptor_sha256,
            "prime-value",
            1,
            (2, 3, 5),
            SequenceValueType.INTEGER,
        )
        self.assertEqual(window.end_index, 3)

    def test_integer_window_rejects_boolean(self):
        with self.assertRaises(ValidationError):
            SequenceWindow(
                self.descriptor().descriptor_sha256,
                "prime-value",
                1,
                (2, True),
                SequenceValueType.INTEGER,
            )

    def test_real_window_normalizes_values(self):
        window = SequenceWindow(
            self.descriptor().descriptor_sha256,
            "real",
            0,
            (1, 2.5),
            SequenceValueType.REAL,
        )
        self.assertEqual(window.values, (1.0, 2.5))

    def test_real_window_rejects_infinity(self):
        with self.assertRaises(ValidationError):
            SequenceWindow(
                self.descriptor().descriptor_sha256,
                "real",
                0,
                (float("inf"),),
                SequenceValueType.REAL,
            )

    def test_batch_request_requires_entries(self):
        with self.assertRaises(ValidationError):
            SequenceBatchRequest(())

    def test_batch_hash_stable(self):
        window = SequenceWindow(
            self.descriptor().descriptor_sha256,
            "prime-value",
            1,
            (2,),
            SequenceValueType.INTEGER,
        )
        self.assertEqual(
            SequenceBatch((window,)).batch_sha256,
            SequenceBatch((window,)).batch_sha256,
        )

    def test_provider_protocol(self):
        provider = InMemorySequenceProvider(
            "prime-value",
            (2, 3, 5),
            index_origin=1,
            strictly_increasing=True,
        )
        self.assertIsInstance(provider, SequenceProvider)

    def test_provider_strictly_increasing_validation(self):
        with self.assertRaises(ValidationError):
            InMemorySequenceProvider(
                "bad",
                (2, 2, 3),
                strictly_increasing=True,
            )

    def test_provider_describe(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            provider = InMemorySequenceProvider(
                "prime-value",
                (2, 3, 5),
                index_origin=1,
                strictly_increasing=True,
            )
            descriptor = provider.describe(session.context)
            self.assertEqual(descriptor.length, 3)
            self.assertTrue(descriptor.strictly_increasing)

    def test_provider_read_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            provider = InMemorySequenceProvider(
                "prime-value",
                (2, 3, 5, 7, 11),
                index_origin=1,
                strictly_increasing=True,
            )
            window = provider.read_window(
                SequenceWindowRequest("prime-value", 2, 3),
                session.context,
            )
            self.assertEqual(window.values, (3, 5, 7))

    def test_provider_rejects_boundary_overrun(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            provider = InMemorySequenceProvider(
                "x",
                (1, 2),
            )
            with self.assertRaises(ValidationError):
                provider.read_window(
                    SequenceWindowRequest("x", 1, 2),
                    session.context,
                )

    def test_registry_register_resolve(self):
        registry = SequenceProviderRegistry()
        provider = InMemorySequenceProvider("x", (1,))
        registry.register(provider)
        self.assertIs(registry.resolve("x"), provider)

    def test_registry_duplicate_rejected(self):
        registry = SequenceProviderRegistry()
        registry.register(InMemorySequenceProvider("x", (1,)))
        with self.assertRaises(ConfigurationError):
            registry.register(InMemorySequenceProvider("x", (2,)))

    def test_adapter_list(self):
        plugin = SequenceExecutionPlugin(
            configuration={
                "providers": [
                    {"sequence_id": "x", "values": [1, 2, 3]}
                ]
            }
        )
        output = plugin.execute(
            {"operation": "list"},
            type("Context", (), {"session_id": "RUN-X"})(),
        )
        self.assertEqual(output["sequence_ids"], ["x"])

    def test_adapter_describe(self):
        plugin = SequenceExecutionPlugin(
            configuration={
                "providers": [
                    {"sequence_id": "x", "values": [1, 2, 3]}
                ]
            }
        )
        output = plugin.execute(
            {"operation": "describe", "sequence_id": "x"},
            type("Context", (), {"session_id": "RUN-X"})(),
        )
        self.assertEqual(output["length"], 3)

    def test_adapter_window(self):
        plugin = SequenceExecutionPlugin(
            configuration={
                "providers": [
                    {
                        "sequence_id": "x",
                        "values": [2, 3, 5, 7],
                        "index_origin": 1,
                    }
                ]
            }
        )
        output = plugin.execute(
            {
                "operation": "window",
                "sequence_id": "x",
                "start_index": 2,
                "count": 2,
            },
            type("Context", (), {"session_id": "RUN-X"})(),
        )
        self.assertEqual(output["values"], [3, 5])

    def test_adapter_batch(self):
        plugin = SequenceExecutionPlugin(
            configuration={
                "providers": [
                    {"sequence_id": "x", "values": [1, 2, 3, 4]}
                ]
            }
        )
        output = plugin.execute(
            {
                "operation": "batch",
                "requests": [
                    {
                        "sequence_id": "x",
                        "start_index": 0,
                        "count": 2,
                    },
                    {
                        "sequence_id": "x",
                        "start_index": 2,
                        "count": 2,
                    },
                ],
            },
            type("Context", (), {"session_id": "RUN-X"})(),
        )
        self.assertEqual(len(output["windows"]), 2)

    def test_adapter_rejects_unknown_operation(self):
        with self.assertRaises(ValidationError):
            SequenceExecutionPlugin().execute(
                {"operation": "missing"},
                type("Context", (), {"session_id": "RUN-X"})(),
            )

    def test_b14_pipeline_integration(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(
                PluginManifest(
                    schema_version="1.0",
                    plugin_id="sequence_api",
                    plugin_version="2.0.0-phase-b2.1",
                    module="sequence_api.adapter",
                    class_name="SequenceExecutionPlugin",
                    capabilities=(
                        "sequence.describe",
                        "sequence.window",
                        "sequence.batch",
                    ),
                    enabled=True,
                    configuration={
                        "providers": [
                            {
                                "sequence_id": "prime-value",
                                "values": [2, 3, 5, 7, 11],
                                "index_origin": 1,
                                "strictly_increasing": True,
                            }
                        ]
                    },
                )
            )
            pipeline = PluginExecutionPipeline(engine, registry)
            record = pipeline.execute(
                execution_id="EXEC-B21-1",
                capability="sequence.window",
                payload={
                    "operation": "window",
                    "sequence_id": "prime-value",
                    "start_index": 2,
                    "count": 3,
                },
            )
            self.assertTrue(record.success)
            self.assertEqual(
                engine.output("EXEC-B21-1")["values"],
                [3, 5, 7],
            )

    def test_pipeline_output_deterministic(self):
        outputs = []
        for execution_id in ("EXEC-B21-A", "EXEC-B21-B"):
            with tempfile.TemporaryDirectory() as temporary:
                session = self.make_session(Path(temporary))
                engine = ExecutionEngine(session=session)
                registry = ManifestRegistry()
                registry.register(
                    PluginManifest(
                        "1.0",
                        "sequence_api",
                        "2.0.0-phase-b2.1",
                        "sequence_api.adapter",
                        "SequenceExecutionPlugin",
                        ("sequence.window",),
                        True,
                        {
                            "providers": [
                                {
                                    "sequence_id": "x",
                                    "values": [10, 20, 30],
                                }
                            ]
                        },
                    )
                )
                pipeline = PluginExecutionPipeline(engine, registry)
                pipeline.execute(
                    execution_id=execution_id,
                    capability="sequence.window",
                    payload={
                        "operation": "window",
                        "sequence_id": "x",
                        "start_index": 0,
                        "count": 3,
                    },
                )
                outputs.append(engine.output(execution_id))
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
