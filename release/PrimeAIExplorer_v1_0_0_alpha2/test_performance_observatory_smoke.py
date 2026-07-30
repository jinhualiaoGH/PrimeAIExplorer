from primeaiexplorer.observatories import ObservatoryManager, PerformanceObservatory

records = [
    {"case_id": "CASE-W004-0001", "window": 4, "prediction": 6, "confidence": 80, "actual_gap": 6},
    {"case_id": "CASE-W004-0002", "window": 4, "prediction": 6, "confidence": 60, "actual_gap": 2},
    {"case_id": "CASE-W008-0001", "window": 8, "prediction": 4, "confidence": 50, "actual_gap": 4},
    {"case_id": "CASE-W008-0002", "window": 8, "prediction": 6, "confidence": 70, "actual_gap": 8},
]

manager = ObservatoryManager([PerformanceObservatory(calibration_bins=5)])
result = manager.run(
    records,
    {
        "experiment_id": "EXP-000001",
        "pilot_id": "pilot_demo",
        "model": "Demo Model",
        "dataset_case_count": 8,
        "ledger_entry_count": 5,
        "pending_entry_count": 1,
    },
)["performance"]

print("PrimeAIExplorer v1.0.0-alpha2 Performance Observatory")
print("=" * 62)
for key in ("record_count", "accuracy", "mean_confidence", "brier_score", "ece", "dataset_coverage", "pilot_completion"):
    print(f"{key}: {result.metrics[key]}")
print("window rows:", len(result.tables["window_performance"]))
print("calibration rows:", len(result.tables["calibration_bins"]))
print("[PASS] Performance Observatory smoke test")
