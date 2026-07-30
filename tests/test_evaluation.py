"""Tests for the PrimeAIExplorer evaluation foundation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from core.evaluation import (
    EvaluationStatus,
    MetricStatus,
    canonical_evaluation_result_id,
    evaluate_exact_match,
    evaluate_numeric_error,
    evaluate_required_json_fields,
    normalize_text,
    parse_decimal,
)


OBSERVATION_ID = "OBS-0000000001"
OBSERVATION_SCHEMA_VERSION = "0.3.0"
RESPONSE_HASH = "a" * 64


class EvaluationIdentifierTests(unittest.TestCase):
    def test_first_identifier(self) -> None:
        self.assertEqual(
            canonical_evaluation_result_id(1),
            "EVR-0000000001",
        )

    def test_large_identifier(self) -> None:
        self.assertEqual(
            canonical_evaluation_result_id(1_234_567),
            "EVR-0001234567",
        )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_evaluation_result_id(0)

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_evaluation_result_id(True)


class NormalizationTests(unittest.TestCase):
    def test_default_normalization(self) -> None:
        self.assertEqual(
            normalize_text("  PrimeNet\r\n"),
            "PrimeNet",
        )

    def test_casefold_and_whitespace(self) -> None:
        self.assertEqual(
            normalize_text(
                "  PRIME   NET ",
                casefold=True,
                collapse_whitespace=True,
            ),
            "prime net",
        )


class NumericParsingTests(unittest.TestCase):
    def test_integer(self) -> None:
        self.assertEqual(str(parse_decimal(42)), "42")

    def test_numeric_text(self) -> None:
        self.assertEqual(str(parse_decimal("1.25")), "1.25")

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            parse_decimal(True)

    def test_non_finite_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_decimal(float("inf"))


class ExactMatchEvaluationTests(unittest.TestCase):
    def test_exact_match(self) -> None:
        result = evaluate_exact_match(
            sequence=1,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="PrimeNet",
            expected="PrimeNet",
        )

        self.assertEqual(result.status, EvaluationStatus.SCORED)
        self.assertEqual(result.metrics[0].value, 1.0)
        self.assertTrue(result.metrics[0].details["matched"])

    def test_casefold_match(self) -> None:
        result = evaluate_exact_match(
            sequence=2,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="PRIMENET",
            expected="primenet",
            casefold=True,
        )

        self.assertEqual(result.metrics[0].value, 1.0)

    def test_non_match(self) -> None:
        result = evaluate_exact_match(
            sequence=3,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="2",
            expected="4",
        )

        self.assertEqual(result.metrics[0].value, 0.0)


class NumericEvaluationTests(unittest.TestCase):
    def test_absolute_and_relative_error(self) -> None:
        result = evaluate_numeric_error(
            sequence=4,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="12",
            expected="10",
        )

        self.assertEqual(result.metrics[0].value, 2.0)
        self.assertAlmostEqual(result.metrics[1].value, 0.2)

    def test_zero_target_nonzero_prediction(self) -> None:
        result = evaluate_numeric_error(
            sequence=5,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="1",
            expected="0",
        )

        self.assertIsNone(result.metrics[1].value)
        self.assertEqual(
            result.metrics[1].status,
            MetricStatus.NOT_APPLICABLE,
        )


class StructuredValidityTests(unittest.TestCase):
    def test_valid_json_object(self) -> None:
        result = evaluate_required_json_fields(
            sequence=6,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            raw_text='{"prediction": 6, "confidence": 0.8}',
            required_fields=("prediction", "confidence"),
        )

        self.assertEqual(result.status, EvaluationStatus.SCORED)
        self.assertTrue(result.validity["is_valid"])
        self.assertEqual(result.metrics[0].value, 1.0)

    def test_missing_field(self) -> None:
        result = evaluate_required_json_fields(
            sequence=7,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            raw_text='{"prediction": 6}',
            required_fields=("prediction", "confidence"),
        )

        self.assertEqual(result.status, EvaluationStatus.INVALID)
        self.assertFalse(result.validity["is_valid"])
        self.assertIn("confidence", result.validity["reason"])

    def test_invalid_json(self) -> None:
        result = evaluate_required_json_fields(
            sequence=8,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            raw_text="{not-json}",
            required_fields=("prediction",),
        )

        self.assertEqual(result.status, EvaluationStatus.INVALID)
        self.assertEqual(result.metrics[0].value, 0.0)


class EvaluationPersistenceTests(unittest.TestCase):
    def test_result_hash_is_stable(self) -> None:
        result = evaluate_exact_match(
            sequence=9,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="6",
            expected="6",
        )

        first_hash = result.integrity["result_sha256"]
        result.finalize_integrity()
        second_hash = result.integrity["result_sha256"]

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)

    def test_json_round_trip(self) -> None:
        result = evaluate_exact_match(
            sequence=10,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="6",
            expected="6",
        )

        payload = json.loads(result.to_json())

        self.assertEqual(
            payload["evaluation_result_id"],
            "EVR-0000000010",
        )
        self.assertEqual(payload["status"], "scored")
        self.assertEqual(
            payload["observation"]["observation_id"],
            OBSERVATION_ID,
        )

    def test_atomic_write(self) -> None:
        result = evaluate_exact_match(
            sequence=11,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="6",
            expected="6",
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evaluation.json"
            saved_path = result.write_atomic(output)

            self.assertEqual(saved_path, output)
            self.assertTrue(output.exists())
            self.assertFalse(
                output.with_name(output.name + ".tmp").exists()
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["evaluation_result_id"],
                "EVR-0000000011",
            )


if __name__ == "__main__":
    unittest.main()
