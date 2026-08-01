from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from execution import ExecutionEngine
from kernel import ExecutionContext, ValidationError
from plugin_runtime import ManifestRegistry, PluginExecutionPipeline, PluginManifest
from prompt_engine import (
    DeterministicPromptGenerator,
    PromptRequest,
    PromptTemplateRegistry,
    PromptTemplateSpec,
)
from runtime import RuntimeConfiguration, RuntimeSession
from sequence_api import (
    InMemorySequenceProvider,
    SequenceDatasetEngine,
    SequenceDatasetRegistry,
    SequenceDatasetSpec,
    SequenceExecutionPlugin,
    SequenceProviderRegistry,
)


SYSTEM_TEMPLATE = (
    "You are participating in a controlled numerical continuation experiment. "
    "Follow the response format exactly."
)

USER_TEMPLATE = """You are given a sequence of consecutive prime gaps.

Observation window size: {observation_count}

Observed gaps:
{observed_values}

Predict the next prime gap.

Return JSON only using this exact structure:

{response_schema}
"""


class PromptGenerationEngineTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="b26-prompt-test",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b2.6",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B26-TEST",
            created_utc="2026-08-01T04:00:00.000000Z",
        )
        session = RuntimeSession(
            context=context,
            configuration=RuntimeConfiguration.empty(),
        )
        session.initialize()
        session.start()
        return session

    def make_generator(self):
        providers = SequenceProviderRegistry()
        providers.register(
            InMemorySequenceProvider(
                sequence_id="prime-gap",
                values=(6, 18, 4, 6, 6, 6, 2, 6, 4, 8),
                index_origin=1,
                title="Prompt fixture",
            )
        )
        datasets = SequenceDatasetRegistry()
        datasets.register(
            SequenceDatasetSpec.from_mapping({
                "dataset_id": "next-gap-w8",
                "sequence_id": "prime-gap",
                "start_index": 1,
                "case_count": 2,
                "observation_count": 8,
                "target_count": 1,
                "stride": 1,
            })
        )
        templates = PromptTemplateRegistry()
        templates.register(
            PromptTemplateSpec.from_mapping({
                "template_id": "prime-gap-json-v1",
                "system_template": SYSTEM_TEMPLATE,
                "user_template": USER_TEMPLATE,
                "response_schema": {
                    "prediction": "<integer>",
                    "confidence": "<integer from 0 to 100>",
                    "explanation": "<brief explanation>",
                },
            })
        )
        return DeterministicPromptGenerator(
            SequenceDatasetEngine(providers, datasets),
            templates,
        )

    def test_template_hash_stable(self):
        template = PromptTemplateSpec.from_mapping({
            "template_id": "t",
            "system_template": "System",
            "user_template": "{observation_count}: {observed_values}",
            "response_schema": {"prediction": "<integer>"},
        })
        self.assertEqual(template.template_sha256, template.template_sha256)

    def test_template_missing_required_placeholder_rejected(self):
        with self.assertRaises(ValidationError):
            PromptTemplateSpec.from_mapping({
                "template_id": "t",
                "system_template": "System",
                "user_template": "{observed_values}",
                "response_schema": {"prediction": "<integer>"},
            })

    def test_duplicate_template_rejected(self):
        registry = PromptTemplateRegistry()
        template = PromptTemplateSpec.from_mapping({
            "template_id": "t",
            "system_template": "System",
            "user_template": "{observation_count}: {observed_values}",
            "response_schema": {"prediction": "<integer>"},
        })
        registry.register(template)
        with self.assertRaises(ValidationError):
            registry.register(template)

    def test_unknown_template_rejected(self):
        with self.assertRaises(ValidationError):
            PromptTemplateRegistry().resolve("missing")

    def test_prompt_request_hash_stable(self):
        request = PromptRequest("d", 0, "t")
        self.assertEqual(request.request_sha256, request.request_sha256)

    def test_generated_prompt_messages(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            prompt = self.make_generator().generate(
                PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                session.context,
            )
            self.assertEqual(prompt.system_message, SYSTEM_TEMPLATE)
            self.assertIn("Observation window size: 8", prompt.user_message)
            self.assertIn("6 18 4 6 6 6 2 6", prompt.user_message)
            self.assertIn('"prediction": "<integer>"', prompt.user_message)

    def test_ground_truth_hidden_by_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            prompt = self.make_generator().generate(
                PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                session.context,
            )
            self.assertIsNone(prompt.ground_truth)
            self.assertNotIn("ground_truth", prompt.to_dict())

    def test_ground_truth_optional(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            prompt = self.make_generator().generate(
                PromptRequest(
                    "next-gap-w8",
                    0,
                    "prime-gap-json-v1",
                    include_ground_truth=True,
                ),
                session.context,
            )
            self.assertEqual(prompt.ground_truth, (4,))
            self.assertEqual(prompt.to_dict()["ground_truth"], [4])

    def test_prompt_identity_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            generator = self.make_generator()
            first = generator.generate(
                PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                session.context,
            )
            second = generator.generate(
                PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                session.context,
            )
            self.assertEqual(first.prompt_id, second.prompt_id)
            self.assertEqual(first.prompt_sha256, second.prompt_sha256)

    def test_different_case_has_different_prompt(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            generator = self.make_generator()
            first = generator.generate(
                PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                session.context,
            )
            second = generator.generate(
                PromptRequest("next-gap-w8", 1, "prime-gap-json-v1"),
                session.context,
            )
            self.assertNotEqual(first.prompt_sha256, second.prompt_sha256)

    def test_prompt_batch(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            batch = self.make_generator().batch(
                (
                    PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                    PromptRequest("next-gap-w8", 1, "prime-gap-json-v1"),
                ),
                session.context,
            )
            self.assertEqual(len(batch.prompts), 2)
            self.assertEqual(len(batch.batch_sha256), 64)

    def test_duplicate_prompt_batch_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            generator = self.make_generator()
            with self.assertRaises(ValidationError):
                generator.batch(
                    (
                        PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                        PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                    ),
                    session.context,
                )

    def plugin_config(self):
        return {
            "providers": [{
                "provider_type": "in_memory",
                "sequence_id": "prime-gap",
                "values": [6, 18, 4, 6, 6, 6, 2, 6, 4, 8],
                "index_origin": 1,
            }],
            "datasets": [{
                "dataset_id": "next-gap-w8",
                "sequence_id": "prime-gap",
                "start_index": 1,
                "case_count": 2,
                "observation_count": 8,
                "target_count": 1,
            }],
            "prompt_templates": [{
                "template_id": "prime-gap-json-v1",
                "system_template": SYSTEM_TEMPLATE,
                "user_template": USER_TEMPLATE,
                "response_schema": {
                    "prediction": "<integer>",
                    "confidence": "<integer from 0 to 100>",
                    "explanation": "<brief explanation>",
                },
            }],
        }

    def test_plugin_template_list(self):
        plugin = SequenceExecutionPlugin(self.plugin_config())
        try:
            result = plugin.execute(
                {"operation": "prompt.template.list"},
                self.make_session(Path(".")).context,
            )
            self.assertEqual(result["template_ids"], ["prime-gap-json-v1"])
        finally:
            plugin.close()

    def test_plugin_template_describe(self):
        plugin = SequenceExecutionPlugin(self.plugin_config())
        try:
            result = plugin.execute(
                {
                    "operation": "prompt.template.describe",
                    "template_id": "prime-gap-json-v1",
                },
                self.make_session(Path(".")).context,
            )
            self.assertEqual(result["template_id"], "prime-gap-json-v1")
            self.assertEqual(len(result["template_sha256"]), 64)
        finally:
            plugin.close()

    def test_plugin_prompt_generate(self):
        with tempfile.TemporaryDirectory() as temporary:
            plugin = SequenceExecutionPlugin(self.plugin_config())
            try:
                result = plugin.execute(
                    {
                        "operation": "prompt.generate",
                        "dataset_id": "next-gap-w8",
                        "case_index": 0,
                        "template_id": "prime-gap-json-v1",
                    },
                    self.make_session(Path(temporary)).context,
                )
                self.assertIn("6 18 4 6 6 6 2 6", result["user_message"])
                self.assertNotIn("ground_truth", result)
            finally:
                plugin.close()

    def test_plugin_prompt_batch(self):
        with tempfile.TemporaryDirectory() as temporary:
            plugin = SequenceExecutionPlugin(self.plugin_config())
            try:
                result = plugin.execute(
                    {
                        "operation": "prompt.batch",
                        "requests": [
                            {
                                "dataset_id": "next-gap-w8",
                                "case_index": 0,
                                "template_id": "prime-gap-json-v1",
                            },
                            {
                                "dataset_id": "next-gap-w8",
                                "case_index": 1,
                                "template_id": "prime-gap-json-v1",
                            },
                        ],
                    },
                    self.make_session(Path(temporary)).context,
                )
                self.assertEqual(len(result["prompts"]), 2)
                self.assertEqual(len(result["batch_sha256"]), 64)
            finally:
                plugin.close()

    def test_pipeline_prompt_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = self.make_session(root)
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(
                PluginManifest(
                    schema_version="1.0",
                    plugin_id="sequence_api",
                    plugin_version="2.0.0-phase-b2.6",
                    module="sequence_api.adapter",
                    class_name="SequenceExecutionPlugin",
                    capabilities=("prompt.generate",),
                    enabled=True,
                    configuration=self.plugin_config(),
                )
            )
            pipeline = PluginExecutionPipeline(engine, registry)
            try:
                record = pipeline.execute(
                    execution_id="EXEC-B26-PROMPT",
                    capability="prompt.generate",
                    payload={
                        "operation": "prompt.generate",
                        "dataset_id": "next-gap-w8",
                        "case_index": 0,
                        "template_id": "prime-gap-json-v1",
                    },
                )
                self.assertTrue(record.success)
                output = engine.output("EXEC-B26-PROMPT")
                self.assertEqual(output["template_id"], "prime-gap-json-v1")
                self.assertEqual(len(output["prompt_sha256"]), 64)
            finally:
                pipeline.close_plugin("sequence_api")


if __name__ == "__main__":
    unittest.main()
