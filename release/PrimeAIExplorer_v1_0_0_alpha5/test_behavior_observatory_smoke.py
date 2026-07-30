from primeaiexplorer.observatories import (
    BehaviorObservatory,
    ObservatoryManager,
    PerformanceObservatory,
)

records = [
    {"case_id": "CASE-W004-0001", "window": 4, "prediction": 6, "confidence": 20, "actual_gap": 12},
    {"case_id": "CASE-W004-0002", "window": 4, "prediction": 6, "confidence": 80, "actual_gap": 6},
    {"case_id": "CASE-W008-0001", "window": 8, "prediction": 4, "confidence": 90, "actual_gap": 12},
    {"case_id": "CASE-W008-0002", "window": 8, "prediction": 4, "confidence": 70, "actual_gap": 4},
]

manager = ObservatoryManager([
    PerformanceObservatory(),
    BehaviorObservatory(),
])
results = manager.run(records, {
    "experiment_id": "EXP-000001",
    "pilot_id": "pilot_alpha3",
    "model": "Demo Model",
    "dataset_case_count": 8,
    "ledger_entry_count": 5,
})
behavior = results["behavior"]

print("PrimeAIExplorer v1.0.0-alpha3 Behavior Observatory")
print("=" * 62)
for key in (
    "record_count", "favorite_prediction", "favorite_prediction_share",
    "switch_count", "switch_rate", "run_count", "max_run_length",
    "prediction_entropy_bits", "confidence_realism_gap",
):
    print(f"{key}: {behavior.metrics[key]}")
print("popularity rows:", len(behavior.tables["prediction_popularity"]))
print("run rows:", len(behavior.tables["persistence_runs"]))
print("transition rows:", len(behavior.tables["prediction_transitions"]))
print("fingerprint rows:", len(behavior.tables["behavior_fingerprint"]))
assert results["performance"].metrics["accuracy"] == 0.5
assert behavior.metrics["switch_count"] == 1
assert behavior.metrics["max_run_length"] == 2
assert len(behavior.tables["behavior_fingerprint"]) == 11
print("[PASS] Behavior Observatory smoke test")
