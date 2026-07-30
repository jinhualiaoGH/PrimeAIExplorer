import unittest

from primeaiexplorer.observatories import DistributionObservatory


RECORDS = [
    {"prediction": 6, "actual_gap": 6, "window": 4},
    {"prediction": 6, "actual_gap": 2, "window": 4},
    {"prediction": 4, "actual_gap": 4, "window": 8},
    {"prediction": 4, "actual_gap": 6, "window": 8},
]


class DistributionObservatoryTests(unittest.TestCase):
    def test_name(self):
        self.assertEqual(DistributionObservatory().name, "distribution")

    def test_metrics(self):
        result = DistributionObservatory().analyze(RECORDS, {})
        self.assertEqual(result.metrics["record_count"], 4)
        self.assertEqual(result.metrics["exact_count"], 2)
        self.assertEqual(result.metrics["underprediction_count"], 1)
        self.assertEqual(result.metrics["overprediction_count"], 1)
        self.assertAlmostEqual(result.metrics["mean_absolute_error"], 1.5)

    def test_prediction_distribution(self):
        result = DistributionObservatory().analyze(RECORDS, {})
        rows = [dict(row) for row in result.tables["prediction_distribution"]]
        self.assertEqual(rows, [
            {"prediction": 4, "count": 2, "share": 0.5},
            {"prediction": 6, "count": 2, "share": 0.5},
        ])

    def test_error_distribution(self):
        result = DistributionObservatory().analyze(RECORDS, {})
        values = [row["signed_error"] for row in result.tables["error_distribution"]]
        self.assertEqual(values, [-2, 0, 4])

    def test_confusion_rows(self):
        result = DistributionObservatory().analyze(RECORDS, {})
        self.assertEqual(len(result.tables["confusion_matrix"]), 4)

    def test_window_rows(self):
        result = DistributionObservatory().analyze(RECORDS, {})
        self.assertEqual(len(result.tables["window_distribution"]), 2)

    def test_invalid_truth(self):
        with self.assertRaises(TypeError):
            DistributionObservatory().analyze([{"prediction": 2}], {})

    def test_empty(self):
        result = DistributionObservatory().analyze([], {})
        self.assertEqual(result.metrics["record_count"], 0)
        self.assertTrue(result.warnings)


if __name__ == "__main__":
    unittest.main()
