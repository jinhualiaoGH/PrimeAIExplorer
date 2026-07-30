import unittest

from primeaiexplorer.observatories import SurpriseObservatory


RECORDS = [
    {"case_id": "A", "prediction": 6, "actual_gap": 6, "confidence": 80, "window": 4},
    {"case_id": "B", "prediction": 6, "actual_gap": 2, "confidence": 90, "window": 4},
    {"case_id": "C", "prediction": 4, "actual_gap": 4, "confidence": 70, "window": 8},
    {"case_id": "D", "prediction": 8, "actual_gap": 6, "confidence": 95, "window": 8},
]


class SurpriseObservatoryTests(unittest.TestCase):
    def test_name(self):
        self.assertEqual(SurpriseObservatory().name, "surprise")

    def test_metrics(self):
        result = SurpriseObservatory().analyze(RECORDS, {})
        self.assertEqual(result.metrics["record_count"], 4)
        self.assertEqual(result.metrics["novel_prediction_count"], 3)
        self.assertAlmostEqual(result.metrics["novel_prediction_rate"], 0.75)
        self.assertEqual(result.metrics["unexpected_error_count"], 2)

    def test_event_rows(self):
        result = SurpriseObservatory().analyze(RECORDS, {})
        rows = result.tables["surprise_events"]
        self.assertEqual(len(rows), 4)
        self.assertIn("surprise_index", rows[0])
        self.assertIn("surprise_rank", rows[0])

    def test_novel_predictions(self):
        result = SurpriseObservatory().analyze(RECORDS, {})
        values = [row["prediction"] for row in result.tables["novel_predictions"]]
        self.assertEqual(values, [6, 4, 8])

    def test_timeline(self):
        result = SurpriseObservatory().analyze(RECORDS, {})
        rows = result.tables["surprise_timeline"]
        self.assertEqual(len(rows), 4)
        self.assertGreaterEqual(rows[-1]["cumulative_max_surprise"], rows[0]["surprise_index"])

    def test_window_rows(self):
        result = SurpriseObservatory().analyze(RECORDS, {})
        self.assertEqual(len(result.tables["window_surprise"]), 2)

    def test_confidence_normalization(self):
        a = SurpriseObservatory().analyze([{"prediction": 2, "truth": 2, "confidence": 50}], {})
        b = SurpriseObservatory().analyze([{"prediction": 2, "truth": 2, "confidence": 0.5}], {})
        self.assertEqual(a.metrics["mean_confidence_surprise"], b.metrics["mean_confidence_surprise"])

    def test_invalid_record(self):
        with self.assertRaises(TypeError):
            SurpriseObservatory().analyze([{"prediction": "6", "truth": 6}], {})

    def test_empty(self):
        result = SurpriseObservatory().analyze([], {})
        self.assertEqual(result.metrics["record_count"], 0)
        self.assertTrue(result.warnings)


if __name__ == "__main__":
    unittest.main()
