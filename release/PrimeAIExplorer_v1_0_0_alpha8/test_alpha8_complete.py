from pathlib import Path
import shutil

from primeaiexplorer.dashboards import HtmlDashboardEngine
from primeaiexplorer.exporters import UnifiedExportEngine
from primeaiexplorer.observatories import (
    BehaviorObservatory,
    CalibrationObservatory,
    DistributionObservatory,
    ObservatoryManager,
    PerformanceObservatory,
    SurpriseObservatory,
)
from primeaiexplorer.visualizations import SvgVisualizationEngine


records = [
    {
        "case_id": "CASE-W004-0001",
        "window": 4,
        "prediction": 6,
        "confidence": 80,
        "actual_gap": 6,
    },
    {
        "case_id": "CASE-W004-0002",
        "window": 4,
        "prediction": 6,
        "confidence": 90,
        "actual_gap": 2,
    },
    {
        "case_id": "CASE-W008-0001",
        "window": 8,
        "prediction": 4,
        "confidence": 70,
        "actual_gap": 4,
    },
    {
        "case_id": "CASE-W008-0002",
        "window": 8,
        "prediction": 8,
        "confidence": 95,
        "actual_gap": 6,
    },
]

context = {
    "experiment_id": "EXP-000001",
    "pilot_id": "pilot_008",
    "model": "GPT-5.6 Thinking",
}

manager = ObservatoryManager([
    PerformanceObservatory(),
    BehaviorObservatory(),
    CalibrationObservatory(),
    DistributionObservatory(),
    SurpriseObservatory(),
])

results = manager.run(
    records=records,
    context=context,
)

output = Path("alpha8_example")
shutil.rmtree(output, ignore_errors=True)

UnifiedExportEngine().export(
    results,
    output,
    context=context,
)

figures = SvgVisualizationEngine().render_all(
    results,
    output / "figures",
)

HtmlDashboardEngine().render(
    results,
    output / "dashboard.html",
    context=context,
)

print("PrimeAIExplorer alpha8 complete visualization test")
print("=" * 68)
print("Execution order:", list(results))
print("Figures:", list(figures))
print("Figure count:", len(figures))
print("Dashboard:", output / "dashboard.html")
print("[PASS] Alpha8 visualization package generated")
