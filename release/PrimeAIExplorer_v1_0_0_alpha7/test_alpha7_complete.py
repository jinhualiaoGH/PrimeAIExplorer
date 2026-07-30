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
    "pilot_id": "pilot_007",
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

UnifiedExportEngine().export(
    results,
    "alpha7_example",
    context=context,
)

HtmlDashboardEngine().render(
    results,
    "alpha7_example/dashboard.html",
    context=context,
)

print("Execution order:", list(results))
print("[PASS] Alpha7 unified analysis package generated")
