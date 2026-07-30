from pathlib import Path
import shutil

from primeaiexplorer.dashboards import HtmlDashboardEngine
from primeaiexplorer.exporters import UnifiedExportEngine
from primeaiexplorer.observatories import (
    BehaviorObservatory, CalibrationObservatory, DistributionObservatory,
    ObservatoryManager, PerformanceObservatory, SurpriseObservatory,
)

records = [
    {"case_id":"CASE-W004-0001","window":4,"prediction":6,"confidence":80,"actual_gap":6},
    {"case_id":"CASE-W004-0002","window":4,"prediction":6,"confidence":90,"actual_gap":2},
    {"case_id":"CASE-W008-0001","window":8,"prediction":4,"confidence":70,"actual_gap":4},
    {"case_id":"CASE-W008-0002","window":8,"prediction":8,"confidence":95,"actual_gap":6},
]
context = {"experiment_id":"EXP-000001","pilot_id":"pilot_007","model":"GPT-5.6 Thinking"}
manager = ObservatoryManager([
    PerformanceObservatory(), BehaviorObservatory(), CalibrationObservatory(),
    DistributionObservatory(), SurpriseObservatory(),
])
results = manager.run(records, context)
out = Path("demo_alpha7")
shutil.rmtree(out, ignore_errors=True)
UnifiedExportEngine().export(results, out, context=context)
HtmlDashboardEngine().render(results, out / "dashboard.html", context=context)

print("PrimeAIExplorer v1.0.0-alpha7 Unified Dashboard")
print("=" * 64)
print("observatories:", len(results))
print("metrics file:", out / "metrics.csv")
print("manifest:", out / "manifest.json")
print("dashboard:", out / "dashboard.html")
print("[PASS] Unified export and HTML dashboard smoke test")
