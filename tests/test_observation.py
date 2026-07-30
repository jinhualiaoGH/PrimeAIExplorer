"""Tests for the PrimeAIExplorer observation foundation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from core.observation import (
    DatasetLink,
    ExperimentLink,
    ObservationRecord,
    ObservationStatus,
    SubjectLink,
    canonical_observation_id,
    sha256_text,
)


class CanonicalObservationIdTests(unittest.TestCase):
    def test_first_identifier(self) -> None:
        self.assertEqual(canonical_observation_id(1), "OBS-0000000001")

    def test_larger_identifier(self) -> None:
        self.assertEqual(
            canonical_observation_id(1_234_567),
            "OBS-0001234567",
        )

    def test_zero_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_observation_id(0)

    def test_boolean_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_observation_id(True)


class ObservationRecordTests(unittest.TestCase):
    def build_record(self) -> ObservationRecord:
        rendered_prompt = (
            "Observe the following prime gaps: 2, 4, 2, 4.\n"
            "Return a structured prediction."
        )

        return ObservationRecord.create_dry_run(
            sequence=1,
            run_id="RUN-20260725-000001",
            condition_id="COND-EXP000001-001",
            experiment=ExperimentLink(
                experiment_id="EXP-000001",
                experiment_version="0.1.0",
                experimental_universe="PrimeNet",
                hypothesis_id="HYP-EXP-000001-001",
            ),
            dataset=DatasetLink(
                dataset_id="DS-000001",
                dataset_version="0.1.0",
                partition="calibration",
                record_id="REC-DS000001-0000000001",
            ),
            prompt_id="PROMPT-000001",
            prompt_version="0.1.0",
            rendered_prompt=rendered_prompt,
            response_schema_id="RESPONSE-000001",
            response_schema_version="0.1.0",
            subject=SubjectLink(
                subject_id="SUBJECT-000001",
                subject_type="deterministic_baseline",
                provider="PrimeAIExplorer",
                connector="dry_run",
                connector_version="0.3.0",
                model_identifier="no-model-call",
                reported_model_version=None,
            ),
            execution_parameters={
                "temperature": 0,
                "maximum_output_tokens": 128,
            },
        )

    def test_dry_run_does_not_claim_model_execution(self) -> None:
        record = self.build_record()

        self.assertEqual(record.status, ObservationStatus.PENDING)
        self.assertEqual(record.execution["mode"], "dry_run")
        self.assertFalse(record.execution["model_call_performed"])
        self.assertIsNone(record.response["raw_text"])

    def test_prompt_hash_is_stable(self) -> None:
        record = self.build_record()
        expected = sha256_text(
            "Observe the following prime gaps: 2, 4, 2, 4.\n"
            "Return a structured prediction."
        )

        self.assertEqual(
            record.prompt.rendered_prompt_sha256,
            expected,
        )

    def test_json_round_trip(self) -> None:
        record = self.build_record()
        payload = json.loads(record.to_json())

        self.assertEqual(payload["observation_id"], "OBS-0000000001")
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(
            payload["experiment"]["experiment_id"],
            "EXP-000001",
        )

    def test_atomic_write(self) -> None:
        record = self.build_record()

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "observation.json"
            result = record.write_atomic(output)

            self.assertEqual(result, output)
            self.assertTrue(output.exists())
            self.assertFalse(
                output.with_name(output.name + ".tmp").exists()
            )

            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                saved["observation_id"],
                "OBS-0000000001",
            )


if __name__ == "__main__":
    unittest.main()
