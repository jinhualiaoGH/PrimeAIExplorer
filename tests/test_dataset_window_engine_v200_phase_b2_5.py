from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from execution import ExecutionEngine
from kernel import ExecutionContext, ValidationError
from plugin_runtime import ManifestRegistry, PluginExecutionPipeline, PluginManifest
from runtime import RuntimeConfiguration, RuntimeSession
from sequence_api import (
    DatasetCaseRequest,
    InMemorySequenceProvider,
    SequenceDatasetEngine,
    SequenceDatasetRegistry,
    SequenceDatasetSpec,
    SequenceExecutionPlugin,
    SequenceProviderRegistry,
)


class DatasetWindowEngineTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="b25-dataset-test",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b2.5",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B25-TEST",
            created_utc="2026-08-01T03:00:00.000000Z",
        )
        session = RuntimeSession(
            context=context,
            configuration=RuntimeConfiguration.empty(),
        )
        session.initialize()
        session.start()
        return session

    def make_engine(self):
        providers = SequenceProviderRegistry()
        providers.register(
            InMemorySequenceProvider(
                sequence_id="gaps",
                values=(2, 4, 2, 6, 6, 8, 4, 2, 10, 12, 2, 16),
                index_origin=1,
                title="Gap fixture",
            )
        )
        datasets = SequenceDatasetRegistry()
        datasets.register(
            SequenceDatasetSpec(
                schema_version="1.0",
                dataset_id="next-gap-w4",
                dataset_version="1.0.0",
                sequence_id="gaps",
                title="Next gap from four observations",
                start_index=1,
                case_count=6,
                observation_count=4,
                target_count=1,
                stride=1,
                metadata={"purpose": "continuation"},
            )
        )
        return SequenceDatasetEngine(providers, datasets)

    def test_spec_hash_stable(self):
        spec = SequenceDatasetSpec.from_mapping({
            "dataset_id": "d",
            "sequence_id": "s",
            "start_index": 1,
            "case_count": 2,
            "observation_count": 4,
            "target_count": 1,
        })
        self.assertEqual(spec.dataset_sha256, spec.dataset_sha256)

    def test_spec_final_required_index(self):
        spec = SequenceDatasetSpec.from_mapping({
            "dataset_id": "d",
            "sequence_id": "s",
            "start_index": 10,
            "case_count": 3,
            "observation_count": 4,
            "target_count": 2,
            "stride": 2,
        })
        self.assertEqual(spec.final_case_start_index, 14)
        self.assertEqual(spec.final_required_index, 19)

    def test_invalid_case_index_rejected(self):
        spec = SequenceDatasetSpec.from_mapping({
            "dataset_id": "d",
            "sequence_id": "s",
            "start_index": 1,
            "case_count": 2,
            "observation_count": 4,
            "target_count": 1,
        })
        with self.assertRaises(ValidationError):
            spec.case_start_index(2)

    def test_duplicate_dataset_rejected(self):
        registry = SequenceDatasetRegistry()
        spec = SequenceDatasetSpec.from_mapping({
            "dataset_id": "d",
            "sequence_id": "s",
            "start_index": 1,
            "case_count": 1,
            "observation_count": 1,
            "target_count": 1,
        })
        registry.register(spec)
        with self.assertRaises(ValidationError):
            registry.register(spec)

    def test_unknown_dataset_rejected(self):
        with self.assertRaises(ValidationError):
            SequenceDatasetRegistry().resolve("missing")

    def test_describe_validates_dataset(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            result = self.make_engine().describe("next-gap-w4", session.context)
            self.assertTrue(result["validated"])
            self.assertEqual(result["dataset"]["case_count"], 6)

    def test_dataset_boundary_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = self.make_engine()
            bad = SequenceDatasetSpec.from_mapping({
                "dataset_id": "too-long",
                "sequence_id": "gaps",
                "start_index": 10,
                "case_count": 2,
                "observation_count": 4,
                "target_count": 1,
            })
            engine.datasets.register(bad)
            with self.assertRaises(ValidationError):
                engine.describe("too-long", session.context)

    def test_case_observation_target_split(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            case = self.make_engine().case(
                DatasetCaseRequest("next-gap-w4", 0),
                session.context,
            )
            self.assertEqual(case.observation, (2, 4, 2, 6))
            self.assertEqual(case.target, (6,))
            self.assertEqual(case.target_start_index, 5)

    def test_later_case_stride(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            case = self.make_engine().case(
                DatasetCaseRequest("next-gap-w4", 3),
                session.context,
            )
            self.assertEqual(case.start_index, 4)
            self.assertEqual(case.observation, (6, 6, 8, 4))
            self.assertEqual(case.target, (2,))

    def test_case_id_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = self.make_engine()
            first = engine.case(DatasetCaseRequest("next-gap-w4", 2), session.context)
            second = engine.case(DatasetCaseRequest("next-gap-w4", 2), session.context)
            self.assertEqual(first.case_id, second.case_id)
            self.assertEqual(first.case_sha256, second.case_sha256)

    def test_batch(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            batch = self.make_engine().batch(
                (
                    DatasetCaseRequest("next-gap-w4", 0),
                    DatasetCaseRequest("next-gap-w4", 1),
                ),
                session.context,
            )
            self.assertEqual(len(batch.cases), 2)
            self.assertEqual(len(batch.batch_sha256), 64)

    def test_duplicate_batch_cases_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = self.make_engine()
            with self.assertRaises(ValidationError):
                engine.batch(
                    (
                        DatasetCaseRequest("next-gap-w4", 0),
                        DatasetCaseRequest("next-gap-w4", 0),
                    ),
                    session.context,
                )

    def test_plugin_registers_dataset(self):
        plugin = SequenceExecutionPlugin(configuration={
            "providers": [{
                "provider_type": "in_memory",
                "sequence_id": "gaps",
                "values": [2, 4, 2, 6, 6],
            }],
            "datasets": [{
                "dataset_id": "d",
                "sequence_id": "gaps",
                "start_index": 0,
                "case_count": 1,
                "observation_count": 4,
                "target_count": 1,
            }],
        })
        try:
            self.assertEqual(plugin.dataset_registry.registered_ids(), ("d",))
        finally:
            plugin.close()

    def test_plugin_dataset_list(self):
        plugin = SequenceExecutionPlugin(configuration={
            "providers": [{
                "provider_type": "in_memory",
                "sequence_id": "gaps",
                "values": [2, 4, 2, 6, 6],
            }],
            "datasets": [{
                "dataset_id": "d",
                "sequence_id": "gaps",
                "start_index": 0,
                "case_count": 1,
                "observation_count": 4,
                "target_count": 1,
            }],
        })
        try:
            result = plugin.execute(
                {"operation": "dataset.list"},
                self.make_session(Path(".")).context,
            )
            self.assertEqual(result["dataset_ids"], ["d"])
        finally:
            plugin.close()

    def test_plugin_dataset_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self.make_session(root)
            plugin = SequenceExecutionPlugin(configuration={
                "providers": [{
                    "provider_type": "in_memory",
                    "sequence_id": "gaps",
                    "values": [2, 4, 2, 6, 6, 8],
                    "index_origin": 1,
                }],
                "datasets": [{
                    "dataset_id": "d",
                    "sequence_id": "gaps",
                    "start_index": 1,
                    "case_count": 2,
                    "observation_count": 4,
                    "target_count": 1,
                }],
            })
            try:
                result = plugin.execute(
                    {"operation": "dataset.case", "dataset_id": "d", "case_index": 0},
                    session.context,
                )
                self.assertEqual(result["observation"], [2, 4, 2, 6])
                self.assertEqual(result["target"], [6])
            finally:
                plugin.close()

    def test_pipeline_dataset_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self.make_session(root)
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(
                PluginManifest(
                    schema_version="1.0",
                    plugin_id="sequence_api",
                    plugin_version="2.0.0-phase-b2.5",
                    module="sequence_api.adapter",
                    class_name="SequenceExecutionPlugin",
                    capabilities=("dataset.case",),
                    enabled=True,
                    configuration={
                        "providers": [{
                            "provider_type": "in_memory",
                            "sequence_id": "gaps",
                            "values": [2, 4, 2, 6, 6, 8],
                            "index_origin": 1,
                        }],
                        "datasets": [{
                            "dataset_id": "d",
                            "sequence_id": "gaps",
                            "start_index": 1,
                            "case_count": 2,
                            "observation_count": 4,
                            "target_count": 1,
                        }],
                    },
                )
            )
            pipeline = PluginExecutionPipeline(engine, registry)
            try:
                record = pipeline.execute(
                    execution_id="EXEC-B25-CASE",
                    capability="dataset.case",
                    payload={
                        "operation": "dataset.case",
                        "dataset_id": "d",
                        "case_index": 0,
                    },
                )
                self.assertTrue(record.success)
                output = engine.output("EXEC-B25-CASE")
                self.assertEqual(output["observation"], [2, 4, 2, 6])
                self.assertEqual(output["target"], [6])
            finally:
                pipeline.close_plugin("sequence_api")


if __name__ == "__main__":
    unittest.main()
