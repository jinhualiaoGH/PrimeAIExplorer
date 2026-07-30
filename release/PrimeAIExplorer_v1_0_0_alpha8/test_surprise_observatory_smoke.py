from primeaiexplorer.observatories import ObservatoryManager, SurpriseObservatory

records = [
    {"case_id": "CASE-W004-0001", "window": 4, "prediction": 6, "confidence": 80, "actual_gap": 6},
    {"case_id": "CASE-W004-0002", "window": 4, "prediction": 6, "confidence": 90, "actual_gap": 2},
    {"case_id": "CASE-W008-0001", "window": 8, "prediction": 4, "confidence": 70, "actual_gap": 4},
    {"case_id": "CASE-W008-0002", "window": 8, "prediction": 8, "confidence": 95, "actual_gap": 6},
]
result = ObservatoryManager([SurpriseObservatory()]).run(
    records,
    {"experiment_id": "EXP-000001", "pilot_id": "pilot_005", "model": "GPT-5.6 Thinking"},
)["surprise"]
print("PrimeAIExplorer v1.0.0-alpha5 Surprise Observatory")
print("=" * 62)
for key in (
    "record_count", "novel_prediction_count", "novel_prediction_rate",
    "mean_surprise_index", "maximum_surprise_index",
    "mean_confidence_surprise", "unexpected_error_rate",
):
    print(f"{key}: {result.metrics[key]}")
print("event rows:", len(result.tables["surprise_events"]))
print("timeline rows:", len(result.tables["surprise_timeline"]))
print("novel rows:", len(result.tables["novel_predictions"]))
print("window rows:", len(result.tables["window_surprise"]))
print("transition rows:", len(result.tables["unexpected_transitions"]))
print("[PASS] Surprise Observatory smoke test")
