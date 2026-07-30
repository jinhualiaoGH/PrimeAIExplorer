from __future__ import annotations

import unittest

from primeaiexplorer.observatories import BehaviorObservatory, ObservatoryManager


class BehaviorObservatoryV1Tests(unittest.TestCase):
    def records(self):
        return [
            {"case_id": "C1", "window": 4, "prediction": 6, "confidence": 20, "actual_gap": 12},
            {"case_id": "C2", "window": 4, "prediction": 6, "confidence": 80, "actual_gap": 6},
            {"case_id": "C3", "window": 8, "prediction": 4, "confidence": 90, "actual_gap": 12},
            {"case_id": "C4", "window": 8, "prediction": 4, "confidence": 70, "actual_gap": 4},
        ]

    def result(self):
        manager = ObservatoryManager([BehaviorObservatory()])
        return manager.run(self.records(), {"experiment_id": "EXP-1"})["behavior"]

    def test_popularity_tie_is_deterministic(self):
        rows = self.result().tables["prediction_popularity"]
        self.assertEqual([row["prediction"] for row in rows], [4, 6])
        self.assertEqual(rows[0]["frequency"], 0.5)

    def test_persistence_metrics(self):
        metrics = self.result().metrics
        self.assertEqual(metrics["switch_count"], 1)
        self.assertAlmostEqual(metrics["switch_rate"], 1 / 3)
        self.assertEqual(metrics["max_run_length"], 2)
        self.assertEqual(metrics["run_count"], 2)

    def test_run_boundaries(self):
        runs = self.result().tables["persistence_runs"]
        self.assertEqual(runs[0]["start_case_id"], "C1")
        self.assertEqual(runs[0]["end_case_id"], "C2")
        self.assertEqual(runs[1]["length"], 2)

    def test_transition_probabilities(self):
        rows = self.result().tables["prediction_transitions"]
        by_pair = {(row["from_prediction"], row["to_prediction"]): row for row in rows}
        self.assertAlmostEqual(by_pair[(6, 6)]["probability"], 0.5)
        self.assertAlmostEqual(by_pair[(6, 4)]["probability"], 0.5)
        self.assertTrue(by_pair[(6, 4)]["is_switch"])

    def test_behavior_fingerprint(self):
        rows = self.result().tables["behavior_fingerprint"]
        metrics = {row["metric"] for row in rows}
        self.assertIn("switch_rate", metrics)
        self.assertIn("favorite_prediction", metrics)
        self.assertIn("confidence_realism_gap", metrics)

    def test_window_behavior(self):
        rows = self.result().tables["window_behavior"]
        self.assertEqual([row["window"] for row in rows], [4, 8])
        self.assertEqual(rows[0]["switch_rate"], 0.0)

    def test_empty_records(self):
        result = ObservatoryManager([BehaviorObservatory()]).run([], {})["behavior"]
        self.assertEqual(result.metrics["record_count"], 0)
        self.assertIsNone(result.metrics["favorite_prediction"])
        self.assertTrue(result.warnings)

    def test_invalid_confidence_rejected(self):
        with self.assertRaises(ValueError):
            ObservatoryManager([BehaviorObservatory()]).run(
                [{"prediction": 6, "confidence": 101}], {}
            )

    def test_truth_infers_correctness(self):
        result = ObservatoryManager([BehaviorObservatory()]).run(
            [{"prediction": 6, "truth": 6, "confidence": 80}], {}
        )["behavior"]
        self.assertEqual(result.metrics["empirical_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
