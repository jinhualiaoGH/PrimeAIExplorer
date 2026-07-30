import unittest

from primeaiexplorer.observatories import CalibrationObservatory


RECORDS = [
    {"prediction": 6, "actual_gap": 6, "confidence": 80, "window": 4},
    {"prediction": 6, "actual_gap": 2, "confidence": 60, "window": 4},
    {"prediction": 4, "actual_gap": 4, "confidence": 70, "window": 8},
    {"prediction": 4, "actual_gap": 6, "confidence": 50, "window": 8},
]


class CalibrationObservatoryTests(unittest.TestCase):
    def test_name(self):
        self.assertEqual(CalibrationObservatory().name, "calibration")

    def test_metrics(self):
        result = CalibrationObservatory(bins=10).analyze(RECORDS, {})
        self.assertEqual(result.metrics["record_count"], 4)
        self.assertAlmostEqual(result.metrics["accuracy"], 0.5)
        self.assertAlmostEqual(result.metrics["mean_confidence"], 0.65)
        self.assertAlmostEqual(result.metrics["brier_score"], 0.185)

    def test_reliability_rows(self):
        result = CalibrationObservatory().analyze(RECORDS, {})
        self.assertEqual(len(result.tables["reliability_bins"]), 4)
        self.assertTrue(all("calibration_state" in row for row in result.tables["reliability_bins"]))

    def test_window_rows(self):
        result = CalibrationObservatory().analyze(RECORDS, {})
        self.assertEqual([row["window"] for row in result.tables["window_calibration"]], [4, 8])

    def test_invalid_bins(self):
        with self.assertRaises(ValueError):
            CalibrationObservatory(bins=0)

    def test_invalid_confidence(self):
        with self.assertRaises(ValueError):
            CalibrationObservatory().analyze([{"prediction": 2, "actual_gap": 2, "confidence": 101}], {})

    def test_correct_conflict(self):
        with self.assertRaises(ValueError):
            CalibrationObservatory().analyze([{"prediction": 2, "actual_gap": 2, "confidence": 50, "correct": False}], {})

    def test_empty(self):
        result = CalibrationObservatory().analyze([], {})
        self.assertEqual(result.metrics["ece"], 0.0)
        self.assertTrue(result.warnings)


if __name__ == "__main__":
    unittest.main()
