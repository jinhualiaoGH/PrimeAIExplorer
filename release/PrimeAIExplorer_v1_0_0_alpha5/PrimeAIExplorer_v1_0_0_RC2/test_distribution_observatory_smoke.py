from primeaiexplorer.observatories import DistributionObservatory, ObservatoryManager

records = [
    {"case_id": "CASE-W004-0001", "window": 4, "prediction": 6, "actual_gap": 6},
    {"case_id": "CASE-W004-0002", "window": 4, "prediction": 6, "actual_gap": 2},
    {"case_id": "CASE-W008-0001", "window": 8, "prediction": 4, "actual_gap": 4},
    {"case_id": "CASE-W008-0002", "window": 8, "prediction": 4, "actual_gap": 6},
]
result = ObservatoryManager([DistributionObservatory()]).run(records, {"experiment_id": "EXP-000001"})["distribution"]
print("PrimeAIExplorer v1.0.0-alpha4 Distribution Observatory")
print("=" * 62)
for key in ("record_count", "mean_absolute_error", "exact_rate", "underprediction_rate", "overprediction_rate", "total_variation_distance", "jensen_shannon_divergence_bits"):
    print(f"{key}: {result.metrics[key]}")
print("prediction rows:", len(result.tables["prediction_distribution"]))
print("truth rows:", len(result.tables["truth_distribution"]))
print("error rows:", len(result.tables["error_distribution"]))
print("confusion rows:", len(result.tables["confusion_matrix"]))
print("[PASS] Distribution Observatory smoke test")
