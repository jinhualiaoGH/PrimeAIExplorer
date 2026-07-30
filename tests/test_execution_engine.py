"""Tests for PrimeAIExplorer v0.8 execution engine."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from core.execution_context import (
    ExecutionContext,
    canonical_run_id,
)
from core.execution_engine import (
    ExecutionCase,
    ExecutionEngine,
)
from core.registry_loader import (
    RegistryError,
    RegistryLoader,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RunIdentifierTests(unittest.TestCase):
    def test_canonical_run_identifier(self) -> None:
        self.assertEqual(
            canonical_run_id(
                1,
                run_date=date(2026, 7, 25),
            ),
            "RUN-20260725-000001",
        )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_run_id(0)

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_run_id(True)


class ExecutionContextTests(unittest.TestCase):
    def test_context_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = ExecutionContext.create(
                sequence=1,
                run_date=date(2026, 7, 25),
                experiment_id="EXP-000001",
                experiment_version="0.1.0",
                dataset_id="DS-000001",
                dataset_version="0.1.0",
                prompt_id="PROMPT-000001",
                prompt_version="0.1.0",
                connector_id="CONNECTOR-000001",
                connector_version="0.1.0",
                subject_id="SUBJECT-000001",
                model_identifier="deterministic-mock",
                execution_mode="local",
                results_root=directory,
                random_seed=20260725,
            )

            self.assertEqual(
                context.run_id,
                "RUN-20260725-000001",
            )
            self.assertTrue(
                context.output_directory.endswith(
                    "RUN-20260725-000001"
                )
            )
            self.assertEqual(
                context.primeaiexplorer_version,
                "0.8.0",
            )


class RegistryLoaderTests(unittest.TestCase):
    def test_valid_free_selection(self) -> None:
        loader = RegistryLoader(PROJECT_ROOT)

        selection = loader.validate_selection(
            experiment_id="EXP-000001",
            dataset_id="DS-000001",
            prompt_id="PROMPT-000001",
            connector_id="CONNECTOR-000001",
            execution_profile_id="EXEC-000001",
            free_mode=True,
        )

        self.assertEqual(
            selection["connector"]["cost_class"],
            "free",
        )
        self.assertEqual(
            selection["connector"]["external_access"],
            "false",
        )

    def test_disabled_paid_connector_rejected(self) -> None:
        loader = RegistryLoader(PROJECT_ROOT)

        with self.assertRaises(RegistryError):
            loader.validate_selection(
                experiment_id="EXP-000001",
                dataset_id="DS-000001",
                prompt_id="PROMPT-000001",
                connector_id="CONNECTOR-000003",
                execution_profile_id="EXEC-000003",
                free_mode=True,
            )

    def test_unknown_identifier_rejected(self) -> None:
        loader = RegistryLoader(PROJECT_ROOT)

        with self.assertRaises(RegistryError):
            loader.validate_selection(
                experiment_id="EXP-999999",
                dataset_id="DS-000001",
                prompt_id="PROMPT-000001",
                connector_id="CONNECTOR-000001",
                execution_profile_id="EXEC-000001",
            )


class ExecutionCaseTests(unittest.TestCase):
    def test_empty_prompt_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ExecutionCase(
                case_id="CASE-000001",
                condition_id="COND-EXP000001-001",
                record_id="REC-DS000001-0000000001",
                user_prompt="",
            )


class ExecutionEngineTests(unittest.TestCase):
    def build_context(
        self,
        results_root: str,
    ) -> ExecutionContext:
        return ExecutionContext.create(
            sequence=1,
            run_date=date(2026, 7, 25),
            experiment_id="EXP-000001",
            experiment_version="0.1.0",
            dataset_id="DS-000001",
            dataset_version="0.1.0",
            prompt_id="PROMPT-000001",
            prompt_version="0.1.0",
            connector_id="CONNECTOR-000001",
            connector_version="0.1.0",
            subject_id="SUBJECT-000001",
            model_identifier="deterministic-mock",
            execution_mode="local",
            results_root=results_root,
            random_seed=20260725,
        )

    def build_cases(self) -> list[ExecutionCase]:
        return [
            ExecutionCase(
                case_id="CASE-000001",
                condition_id="COND-EXP000001-001",
                record_id="REC-DS000001-0000000001",
                user_prompt=(
                    "Prime gaps: 2, 4, 2, 4, 6, 2. "
                    "Return a structured prediction."
                ),
            ),
            ExecutionCase(
                case_id="CASE-000002",
                condition_id="COND-EXP000001-002",
                record_id="REC-DS000001-0000000002",
                user_prompt=(
                    "Prime gaps: 6, 4, 2, 4, 6, 6. "
                    "Return a structured prediction."
                ),
            ),
        ]

    def test_empty_case_list_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=self.build_context(directory),
            )

            with self.assertRaises(ValueError):
                engine.run([])

    def test_end_to_end_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.build_context(directory)
            engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=context,
            )

            manifest = engine.run(self.build_cases())

            self.assertEqual(
                manifest["status"],
                "completed",
            )
            self.assertEqual(
                manifest["accounting"]["planned_cases"],
                2,
            )
            self.assertEqual(
                manifest["accounting"]["executed_cases"],
                2,
            )
            self.assertEqual(
                manifest["accounting"]["observations"],
                2,
            )
            self.assertEqual(
                manifest["accounting"]["evaluations"],
                2,
            )
            self.assertEqual(
                manifest["accounting"][
                    "external_access_count"
                ],
                0,
            )
            self.assertEqual(
                manifest["accounting"]["paid_call_count"],
                0,
            )

            output = Path(context.output_directory)

            self.assertTrue(
                (output / "run_manifest.json").exists()
            )
            self.assertTrue(
                (output / "events.jsonl").exists()
            )
            self.assertTrue(
                (output / "run_statistics.json").exists()
            )
            self.assertTrue(
                (
                    output
                    / "report"
                    / "scientific_report.md"
                ).exists()
            )

            observation_files = list(
                (output / "observations").glob("*.json")
            )
            evaluation_files = list(
                (output / "evaluations").glob("*.json")
            )

            self.assertEqual(len(observation_files), 2)
            self.assertEqual(len(evaluation_files), 2)

    def test_mock_run_has_no_external_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.build_context(directory)
            engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=context,
            )

            engine.run(self.build_cases())

            manifest = json.loads(
                (
                    Path(context.output_directory)
                    / "run_manifest.json"
                ).read_text(encoding="utf-8")
            )

            self.assertEqual(
                manifest["accounting"][
                    "external_access_count"
                ],
                0,
            )
            self.assertEqual(
                manifest["accounting"]["paid_call_count"],
                0,
            )

    def test_structured_responses_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.build_context(directory)
            engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=context,
            )

            manifest = engine.run(self.build_cases())

            self.assertEqual(
                manifest["accounting"]["valid_evaluations"],
                2,
            )
            self.assertEqual(
                manifest["accounting"]["invalid_evaluations"],
                0,
            )

    def test_scientific_response_content_is_deterministic(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as first_directory:
            first_context = self.build_context(
                first_directory
            )
            first_engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=first_context,
            )
            first_engine.run(self.build_cases())

            first_observation = json.loads(
                (
                    Path(first_context.output_directory)
                    / "observations"
                    / "OBS-0000000001.json"
                ).read_text(encoding="utf-8")
            )

        with tempfile.TemporaryDirectory() as second_directory:
            second_context = self.build_context(
                second_directory
            )
            second_engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=second_context,
            )
            second_engine.run(self.build_cases())

            second_observation = json.loads(
                (
                    Path(second_context.output_directory)
                    / "observations"
                    / "OBS-0000000001.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(
            first_observation["response"]["raw_text"],
            second_observation["response"]["raw_text"],
        )
        self.assertEqual(
            first_observation["response"][
                "response_sha256"
            ],
            second_observation["response"][
                "response_sha256"
            ],
        )


if __name__ == "__main__":
    unittest.main()
