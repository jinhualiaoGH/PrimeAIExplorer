# PrimeAIExplorer v2.0 Phase C4

C4 consumes experiment `responses.jsonl` files and provides accuracy, MAE, median absolute error, RMSE, latency, confidence, Brier score, expected calibration error, deterministic bootstrap intervals, grouped metrics, paired model comparisons, leaderboards, and JSON/CSV exports.

```powershell
py -m metrics_engine.cli analyze .\experiments\EXP-ID\results\responses.jsonl --output .\analysis\EXP-ID
py -m metrics_engine.cli compare --model model-a=.\examples\phase_c4\model_a_responses.jsonl --model model-b=.\examples\phase_c4\model_b_responses.jsonl --output .\analysis\phase_c4_demo
```
