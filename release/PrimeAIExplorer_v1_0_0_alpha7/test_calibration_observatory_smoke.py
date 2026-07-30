from primeaiexplorer.observatories import CalibrationObservatory, ObservatoryManager

records = [
    {"case_id": "CASE-W004-0001", "window": 4, "prediction": 6, "confidence": 80, "actual_gap": 6},
    {"case_id": "CASE-W004-0002", "window": 4, "prediction": 6, "confidence": 60, "actual_gap": 2},
    {"case_id": "CASE-W008-0001", "window": 8, "prediction": 4, "confidence": 70, "actual_gap": 4},
    {"case_id": "CASE-W008-0002", "window": 8, "prediction": 4, "confidence": 50, "actual_gap": 6},
]
result = ObservatoryManager([CalibrationObservatory()]).run(records, {"experiment_id": "EXP-000001"})["calibration"]
print("PrimeAIExplorer v1.0.0-alpha4 Calibration Observatory")
print("=" * 62)
for key in ("record_count", "accuracy", "mean_confidence", "ece", "maximum_calibration_error", "signed_calibration_bias"):
    print(f"{key}: {result.metrics[key]}")
print("reliability rows:", len(result.tables["reliability_bins"]))
print("window rows:", len(result.tables["window_calibration"]))
print("[PASS] Calibration Observatory smoke test")
