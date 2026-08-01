from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from kernel import ExecutionContext, ValidationError
from evaluation_engine import (
    RawModelResponse,
    ResponseEvaluationEngine,
    parse_prediction_response,
)
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


SYSTEM_TEMPLATE = "Controlled experiment."
USER_TEMPLATE = "{observation_count}\n{observed_values}\n{response_schema}"


class ResponseEvaluationEngineTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="b27-test",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b2.7",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B27-TEST",
            created_utc="2026-08-01T04:30:00.000000Z",
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

    def audit_prompt(self, case_index=0):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            return self.make_generator().generate(
                PromptRequest(
                    "next-gap-w8",
                    case_index,
                    "prime-gap-json-v1",
                    include_ground_truth=True,
                ),
                session.context,
            )

    def test_parse_valid_json(self):
        parsed = parse_prediction_response(
            '{"prediction":4,"confidence":80,"explanation":"pattern"}'
        )
        self.assertEqual(parsed.prediction, 4)
        self.assertEqual(parsed.confidence, 80)

    def test_parse_code_fence(self):
        parsed = parse_prediction_response(
            '```json\n{"prediction":4,"confidence":80,"explanation":"pattern"}\n```'
        )
        self.assertEqual(parsed.prediction, 4)

    def test_invalid_json_rejected(self):
        with self.assertRaises(ValidationError):
            parse_prediction_response("not-json")

    def test_missing_field_rejected(self):
        with self.assertRaises(ValidationError):
            parse_prediction_response(
                '{"prediction":4,"confidence":80}'
            )

    def test_extra_field_rejected(self):
        with self.assertRaises(ValidationError):
            parse_prediction_response(
                '{"prediction":4,"confidence":80,"explanation":"x","extra":1}'
            )

    def test_invalid_confidence_rejected(self):
        with self.assertRaises(ValidationError):
            parse_prediction_response(
                '{"prediction":4,"confidence":101,"explanation":"x"}'
            )

    def test_exact_match_evaluation(self):
        prompt = self.audit_prompt(0)
        response = RawModelResponse(
            prompt_id=prompt.prompt_id,
            response_text='{"prediction":4,"confidence":90,"explanation":"x"}',
            model_id="model-a",
        )
        record = ResponseEvaluationEngine().evaluate(prompt, response)
        self.assertTrue(record.exact_match)
        self.assertEqual(record.absolute_error, 0.0)
        self.assertEqual(record.confidence_error, 10.0)

    def test_incorrect_evaluation(self):
        prompt = self.audit_prompt(0)
        response = RawModelResponse(
            prompt_id=prompt.prompt_id,
            response_text='{"prediction":6,"confidence":80,"explanation":"x"}',
            model_id="model-a",
        )
        record = ResponseEvaluationEngine().evaluate(prompt, response)
        self.assertFalse(record.exact_match)
        self.assertEqual(record.absolute_error, 2.0)
        self.assertEqual(record.squared_error, 4.0)
        self.assertEqual(record.confidence_error, 80.0)

    def test_prompt_mismatch_rejected(self):
        prompt = self.audit_prompt(0)
        response = RawModelResponse(
            prompt_id="wrong",
            response_text='{"prediction":4,"confidence":80,"explanation":"x"}',
        )
        with self.assertRaises(ValidationError):
            ResponseEvaluationEngine().evaluate(prompt, response)

    def test_ground_truth_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            prompt = self.make_generator().generate(
                PromptRequest("next-gap-w8", 0, "prime-gap-json-v1"),
                session.context,
            )
            response = RawModelResponse(
                prompt_id=prompt.prompt_id,
                response_text='{"prediction":4,"confidence":80,"explanation":"x"}',
            )
            with self.assertRaises(ValidationError):
                ResponseEvaluationEngine().evaluate(prompt, response)

    def test_evaluation_deterministic(self):
        prompt = self.audit_prompt(0)
        response = RawModelResponse(
            prompt_id=prompt.prompt_id,
            response_text='{"prediction":4,"confidence":80,"explanation":"x"}',
            model_id="model-a",
        )
        first = ResponseEvaluationEngine().evaluate(prompt, response)
        second = ResponseEvaluationEngine().evaluate(prompt, response)
        self.assertEqual(first.evaluation_sha256, second.evaluation_sha256)

    def test_batch_summary(self):
        first_prompt = self.audit_prompt(0)
        second_prompt = self.audit_prompt(1)
        responses = (
            RawModelResponse(
                prompt_id=first_prompt.prompt_id,
                response_text='{"prediction":4,"confidence":90,"explanation":"x"}',
                model_id="model-a",
            ),
            RawModelResponse(
                prompt_id=second_prompt.prompt_id,
                response_text='{"prediction":6,"confidence":50,"explanation":"x"}',
                model_id="model-a",
            ),
        )
        batch = ResponseEvaluationEngine().evaluate_batch(
            (first_prompt, second_prompt),
            responses,
        )
        self.assertEqual(len(batch.records), 2)
        self.assertEqual(batch.exact_match_count, 1)
        self.assertEqual(batch.exact_match_rate, 0.5)

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

    def test_plugin_parse(self):
        plugin = SequenceExecutionPlugin(self.plugin_config())
        try:
            result = plugin.execute(
                {
                    "operation": "response.parse",
                    "response_text": '{"prediction":4,"confidence":80,"explanation":"x"}',
                },
                self.make_session(Path(".")).context,
            )
            self.assertEqual(result["prediction"], 4)
        finally:
            plugin.close()

    def test_plugin_evaluate(self):
        plugin = SequenceExecutionPlugin(self.plugin_config())
        try:
            generated = plugin.execute(
                {
                    "operation": "prompt.generate",
                    "dataset_id": "next-gap-w8",
                    "case_index": 0,
                    "template_id": "prime-gap-json-v1",
                },
                self.make_session(Path(".")).context,
            )
            result = plugin.execute(
                {
                    "operation": "response.evaluate",
                    "dataset_id": "next-gap-w8",
                    "case_index": 0,
                    "template_id": "prime-gap-json-v1",
                    "prompt_id": generated["prompt_id"],
                    "response_text": '{"prediction":4,"confidence":90,"explanation":"x"}',
                    "model_id": "model-a",
                },
                self.make_session(Path(".")).context,
            )
            self.assertTrue(result["exact_match"])
        finally:
            plugin.close()

    def test_plugin_evaluate_batch(self):
        plugin = SequenceExecutionPlugin(self.plugin_config())
        try:
            context = self.make_session(Path(".")).context
            p0 = plugin.execute(
                {
                    "operation": "prompt.generate",
                    "dataset_id": "next-gap-w8",
                    "case_index": 0,
                    "template_id": "prime-gap-json-v1",
                },
                context,
            )
            p1 = plugin.execute(
                {
                    "operation": "prompt.generate",
                    "dataset_id": "next-gap-w8",
                    "case_index": 1,
                    "template_id": "prime-gap-json-v1",
                },
                context,
            )
            result = plugin.execute(
                {
                    "operation": "response.evaluate_batch",
                    "items": [
                        {
                            "dataset_id": "next-gap-w8",
                            "case_index": 0,
                            "template_id": "prime-gap-json-v1",
                            "prompt_id": p0["prompt_id"],
                            "response_text": '{"prediction":4,"confidence":90,"explanation":"x"}',
                            "model_id": "model-a",
                        },
                        {
                            "dataset_id": "next-gap-w8",
                            "case_index": 1,
                            "template_id": "prime-gap-json-v1",
                            "prompt_id": p1["prompt_id"],
                            "response_text": '{"prediction":6,"confidence":50,"explanation":"x"}',
                            "model_id": "model-a",
                        },
                    ],
                },
                context,
            )
            self.assertEqual(result["summary"]["count"], 2)
            self.assertEqual(result["summary"]["exact_match_count"], 1)
        finally:
            plugin.close()


if __name__ == "__main__":
    unittest.main()
