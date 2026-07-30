from primeaiexplorer.observatories import (
    BehaviorObservatory,
    ObservatoryManager,
    PerformanceObservatory,
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
        "confidence": 60,
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
        "prediction": 4,
        "confidence": 50,
        "actual_gap": 6,
    },
]

manager = ObservatoryManager([
    PerformanceObservatory(),
    BehaviorObservatory(),
])

results = manager.run(
    records=records,
    context={
        "experiment_id": "EXP-000001",
        "pilot_id": "pilot_003",
        "model": "GPT-5.6 Thinking",
        "dataset_case_count": 8,
        "ledger_entry_count": 5,
    },
)

performance = results["performance"]
behavior = results["behavior"]

print("PrimeAIExplorer combined observatory test")
print("=" * 60)
print("Execution order:", list(results.keys()))
print("Accuracy:", performance.metrics["accuracy"])
print("Brier score:", performance.metrics["brier_score"])
print("Favorite prediction:", behavior.metrics["favorite_prediction"])
print("Switch rate:", behavior.metrics["switch_rate"])
print("Maximum run length:", behavior.metrics["max_run_length"])
print("Fingerprint rows:", len(behavior.tables["behavior_fingerprint"]))
print("[PASS] Combined Performance and Behavior Observatory test")
