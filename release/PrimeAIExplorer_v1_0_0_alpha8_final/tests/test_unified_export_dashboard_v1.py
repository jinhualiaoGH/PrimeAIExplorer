import csv
import json
import tempfile
import unittest
from pathlib import Path

from primeaiexplorer.dashboards import HtmlDashboardEngine
from primeaiexplorer.exporters import UnifiedExportEngine
from primeaiexplorer.observatories import ObservatoryManager, PerformanceObservatory, BehaviorObservatory

RECORDS = [
    {"case_id": "A", "prediction": 6, "actual_gap": 6, "confidence": 80, "window": 4},
    {"case_id": "B", "prediction": 6, "actual_gap": 2, "confidence": 60, "window": 4},
    {"case_id": "C", "prediction": 4, "actual_gap": 4, "confidence": 70, "window": 8},
]


def make_results():
    return ObservatoryManager([PerformanceObservatory(), BehaviorObservatory()]).run(RECORDS, {})


class UnifiedExportDashboardTests(unittest.TestCase):
    def test_export_writes_core_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            UnifiedExportEngine().export(make_results(), tmp)
            for name in ("summary.json", "observatories.json", "metrics.csv", "observatory_catalog.csv", "manifest.json"):
                self.assertTrue((Path(tmp) / name).is_file(), name)

    def test_summary_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            exported = UnifiedExportEngine().export(make_results(), tmp)
            self.assertEqual(exported["summary"]["observatory_count"], 2)
            self.assertGreater(exported["summary"]["metric_count"], 0)
            self.assertGreater(exported["summary"]["table_count"], 0)

    def test_metrics_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            UnifiedExportEngine().export(make_results(), tmp)
            with (Path(tmp) / "metrics.csv").open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertTrue(any(row["metric"] == "accuracy" for row in rows))

    def test_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            UnifiedExportEngine().export(make_results(), tmp)
            manifest = json.loads((Path(tmp) / "manifest.json").read_text(encoding="utf-8"))
            self.assertGreater(len(manifest["artifacts"]), 4)
            self.assertTrue(all(len(item["sha256"]) == 64 for item in manifest["artifacts"]))

    def test_empty_export_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                UnifiedExportEngine().export({}, tmp)

    def test_dashboard_is_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = HtmlDashboardEngine().render(make_results(), Path(tmp) / "dashboard.html")
            text = path.read_text(encoding="utf-8")
            self.assertIn("<!doctype html>", text.lower())
            self.assertIn("Performance Observatory", text)
            self.assertNotIn("https://", text)

    def test_dashboard_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = HtmlDashboardEngine().render(make_results(), Path(tmp) / "dashboard.html", context={"model": "GPT-5.6 Thinking"})
            self.assertIn("GPT-5.6 Thinking", path.read_text(encoding="utf-8"))

    def test_dashboard_empty_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                HtmlDashboardEngine().render({}, Path(tmp) / "dashboard.html")


if __name__ == "__main__":
    unittest.main()
