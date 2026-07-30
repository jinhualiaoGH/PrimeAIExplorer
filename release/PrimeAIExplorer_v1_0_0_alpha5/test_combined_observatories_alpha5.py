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

manager = ObservatoryManager([
    PerformanceObservatory(),
    BehaviorObservatory(),
    CalibrationObservatory(),
    DistributionObservatory(),
    SurpriseObservatory(),
])

results = manager.run(
    records=records,
    context={
        "experiment_id": "EXP-000001",
        "pilot_id": "pilot_005",
        "model": "GPT-5.6 Thinking",
        "dataset_case_count": 8,
        "ledger_entry_count": 5,
    },
)

print("PrimeAIExplorer alpha5 combined observatory test")
print("=" * 64)
print("Execution order:", list(results.keys()))
print("Accuracy:", results["performance"].metrics["accuracy"])
print("Switch rate:", results["behavior"].metrics["switch_rate"])
print("ECE:", results["calibration"].metrics["ece"])
print(
    "Jensen-Shannon:",
    results["distribution"].metrics[
        "jensen_shannon_divergence_bits"
    ],
)
print(
    "Mean surprise:",
    results["surprise"].metrics["mean_surprise_index"],
)
print(
    "Novel prediction rate:",
    results["surprise"].metrics["novel_prediction_rate"],
)
print("[PASS] Five-observatory manager test")
