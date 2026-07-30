from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from primeaiexplorer.compare import build_comparison, discover_analyses, load_analysis


class ComparativeObservatoryTests(unittest.TestCase):
    def _analysis(self, root: Path, name: str, model: str, accuracy: float, brier: float) -> Path:
        folder = root / name
        folder.mkdir()
        summary = {
            "record_count": 5,
            "accuracy": accuracy,
            "brier_score": brier,
            "ece": 0.2,
            "prediction_entropy_bits": 0.7,
            "distinct_predictions": 2,
            "mean_confidence": 20.0,
            "mean_signed_error": -2.0,
            "mean_absolute_error": 3.0,
            "persistence": {"switch_rate": 0.25, "max_run_length": 4},
            "window_observatory": [{"window": 4, "count": 1, "accuracy": accuracy}],
            "model_fingerprint": [
                {"metric": "favorite_prediction", "value": 6},
                {"metric": "favorite_prediction_share", "value": 0.8},
                {"metric": "prediction_entropy_bits", "value": 0.7},
                {"metric": "normalized_prediction_entropy", "value": 0.7},
                {"metric": "mean_confidence", "value": 20.0},
                {"metric": "ece", "value": 0.2},
                {"metric": "mean_signed_error", "value": -2.0},
                {"metric": "mean_absolute_error", "value": 3.0},
                {"metric": "switch_rate", "value": 0.25},
                {"metric": "mean_run_length", "value": 2.5},
                {"metric": "max_run_length", "value": 4},
            ],
        }
        manifest = {
            "model": model,
            "pilot_id": name,
            "experiment_id": "EXP-000001",
            "summary_sha256": "test",
        }
        (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return folder

    def test_build_comparison_and_rankings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = load_analysis(self._analysis(root, "pilot_a", "Model A", 0.4, 0.2))
            b = load_analysis(self._analysis(root, "pilot_b", "Model B", 0.6, 0.1))
            result = build_comparison([a, b])
            self.assertEqual(result["analysis_count"], 2)
            self.assertEqual(len(result["comparison_rows"]), 2)
            best_accuracy = next(row for row in result["rankings"] if row["metric"] == "accuracy")
            self.assertIn("Model B", best_accuracy["best_label"])
            best_brier = next(row for row in result["rankings"] if row["metric"] == "brier_score")
            self.assertIn("Model B", best_brier["best_label"])


    def test_discover_analyses_skips_comparisons(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = self._analysis(root, "analysis_a", "Model A", 0.4, 0.2)
            b = self._analysis(root, "analysis_b", "Model B", 0.6, 0.1)
            comparison = root / "comparison_v070"
            comparison.mkdir()
            (comparison / "summary.json").write_text("{}", encoding="utf-8")
            (comparison / "manifest.json").write_text(json.dumps({"model": "bad"}), encoding="utf-8")
            found = discover_analyses(root)
            self.assertEqual(found, sorted([a.resolve(), b.resolve()], key=lambda path: str(path).lower()))


    def test_missing_legacy_metric_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a_path = self._analysis(root, "pilot_a", "Model A", 0.4, 0.2)
            b_path = self._analysis(root, "pilot_b", "Model B", 0.6, 0.1)
            summary = json.loads((a_path / "summary.json").read_text(encoding="utf-8"))
            summary["mean_absolute_error"] = None
            (a_path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            result = build_comparison([load_analysis(a_path), load_analysis(b_path)])
            best = next(row for row in result["rankings"] if row["metric"] == "mean_absolute_error")
            self.assertIn("Model B", best["best_label"])

    def test_requires_two_analyses(self) -> None:
        with self.assertRaises(ValueError):
            build_comparison([{"summary": {}}])


if __name__ == "__main__":
    unittest.main()
