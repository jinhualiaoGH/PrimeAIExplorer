from __future__ import annotations

import unittest

from primeaiexplorer.observatories import ObservatoryManager, PerformanceObservatory


RECORDS = [
    {"case_id": "CASE-W004-0001", "window": 4, "prediction": 6, "confidence": 80, "actual_gap": 6, "correct": True},
    {"case_id": "CASE-W004-0002", "window": 4, "prediction": 6, "confidence": 60, "actual_gap": 2, "correct": False},
    {"case_id": "CASE-W008-0001", "window": 8, "prediction": 4, "confidence": 50, "ground_truth": 4},
    {"case_id": "CASE-W008-0002", "window": 8, "prediction": 6, "confidence": 70, "truth": 8},
]


class PerformanceObservatoryTests(unittest.TestCase):
    def test_public_registration_and_execution(self) -> None:
        manager = ObservatoryManager([PerformanceObservatory()])
        result = manager.run(RECORDS, {"experiment_id": "EXP-000001"})["performance"]
        self.assertEqual(result.metrics["record_count"], 4)
        self.assertEqual(result.metrics["correct_count"], 2)
        self.assertEqual(result.metrics["accuracy"], 0.5)

    def test_core_metrics_match_expected_values(self) -> None:
        result = PerformanceObservatory().analyze(RECORDS, {})
        self.assertAlmostEqual(result.metrics["mean_confidence"], 65.0)
        self.assertAlmostEqual(result.metrics["brier_score"], 0.285)
        self.assertAlmostEqual(result.metrics["mean_absolute_error"], 1.5)
        self.assertAlmostEqual(result.metrics["mean_signed_error"], 0.5)

    def test_coverage_and_completion(self) -> None:
        result = PerformanceObservatory().analyze(
            RECORDS,
            {"dataset_case_count": 8, "ledger_entry_count": 5, "pending_entry_count": 1},
        )
        self.assertEqual(result.metrics["dataset_coverage"], 0.5)
        self.assertEqual(result.metrics["pilot_completion"], 0.8)
        self.assertEqual(result.metrics["pending_entry_count"], 1)

    def test_calibration_and_window_tables(self) -> None:
        result = PerformanceObservatory(calibration_bins=5).analyze(RECORDS, {})
        self.assertTrue(result.tables["calibration_bins"])
        windows = result.tables["window_performance"]
        self.assertEqual([row["window"] for row in windows], [4, 8])
        self.assertEqual([row["count"] for row in windows], [2, 2])

    def test_empty_records_are_valid_with_warning(self) -> None:
        result = PerformanceObservatory().analyze([], {})
        self.assertEqual(result.metrics["accuracy"], 0.0)
        self.assertTrue(result.warnings)

    def test_invalid_confidence_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 100"):
            PerformanceObservatory().analyze([
                {"prediction": 6, "confidence": 101, "actual_gap": 6}
            ], {})

    def test_conflicting_correct_flag_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "conflicts"):
            PerformanceObservatory().analyze([
                {"prediction": 6, "confidence": 80, "actual_gap": 6, "correct": False}
            ], {})

    def test_invalid_calibration_bins_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PerformanceObservatory(calibration_bins=0)


if __name__ == "__main__":
    unittest.main()
