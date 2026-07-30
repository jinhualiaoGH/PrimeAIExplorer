import json
import tempfile
import unittest
from pathlib import Path

from primeaiexplorer.dashboards import HtmlDashboardEngine
from primeaiexplorer.observatories import (
    BehaviorObservatory, CalibrationObservatory, DistributionObservatory,
    ObservatoryManager, PerformanceObservatory, SurpriseObservatory,
)
from primeaiexplorer.visualizations import SvgVisualizationEngine

RECORDS = [
    {"case_id":"A","prediction":6,"actual_gap":6,"confidence":80,"window":4},
    {"case_id":"B","prediction":6,"actual_gap":2,"confidence":90,"window":4},
    {"case_id":"C","prediction":4,"actual_gap":4,"confidence":70,"window":8},
    {"case_id":"D","prediction":8,"actual_gap":6,"confidence":95,"window":8},
]

def results():
    return ObservatoryManager([
        PerformanceObservatory(), BehaviorObservatory(), CalibrationObservatory(),
        DistributionObservatory(), SurpriseObservatory(),
    ]).run(RECORDS, {})

class VisualizationDashboardTests(unittest.TestCase):
    def test_render_all_generates_core_charts(self):
        charts = SvgVisualizationEngine().render_all(results())
        for name in ("performance_overview", "reliability_diagram", "confusion_heatmap", "surprise_timeline"):
            self.assertIn(name, charts)

    def test_svg_is_self_contained(self):
        svg = SvgVisualizationEngine().render_all(results())["performance_overview"]
        self.assertIn("<svg", svg)
        self.assertNotIn("https://", svg)

    def test_render_all_writes_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            charts = SvgVisualizationEngine().render_all(results(), tmp)
            self.assertTrue((Path(tmp) / "figures.json").is_file())
            self.assertEqual(len(list(Path(tmp).glob("*.svg"))), len(charts))

    def test_figure_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            SvgVisualizationEngine().render_all(results(), tmp)
            catalog = json.loads((Path(tmp) / "figures.json").read_text())
            self.assertTrue(any(item["name"] == "reliability_diagram" for item in catalog))

    def test_empty_results_rejected(self):
        with self.assertRaises(ValueError):
            SvgVisualizationEngine().render_all({})

    def test_dashboard_embeds_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = HtmlDashboardEngine().render(results(), Path(tmp) / "dashboard.html")
            text = path.read_text()
            self.assertIn("<svg", text)
            self.assertIn("Reliability Diagram", text)

    def test_dashboard_has_collapsible_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = HtmlDashboardEngine().render(results(), Path(tmp) / "dashboard.html")
            text = path.read_text()
            self.assertIn("<details><summary>Metrics</summary>", text)

    def test_confusion_chart_contains_cells(self):
        svg = SvgVisualizationEngine().render_all(results())["confusion_heatmap"]
        self.assertIn('class="cell"', svg)

if __name__ == "__main__":
    unittest.main()
