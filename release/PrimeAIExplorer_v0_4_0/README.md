# PrimeAIExplorer v0.4.0 — Prediction Observatory

This release extends the interactive workspace with research analytics:

- prediction and truth distributions
- over/under-prediction bias
- prediction-vs-truth confusion matrix
- calibration visualization and CSV
- cumulative Accuracy/Brier/ECE/Entropy trends
- timing/throughput statistics when timestamps or response durations are present
- CSV exports for Python, R, MATLAB, and spreadsheet analysis

The v0.3.1 workspace and all prior collection commands remain available.

## Install

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_4_0
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
.\run_tests.ps1
.\run_demo.ps1
```

## Real experiment

```powershell
$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_4_0"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v040\pilot_002"
cd $Release

.\.venv\Scripts\paiexp.exe analyze `
  --responses "$Pilot" --dataset "$Dataset" --output "$Output" `
  --model "GPT-5.6 Thinking" --experiment-id "EXP-000001" --pilot-id "pilot_002"

.\.venv\Scripts\paiexp.exe verify --analysis "$Output"
Start-Process "$Output\report.html"
```

Generated exports include `prediction_bias.csv`, `confusion_matrix.csv`, `calibration_bins.csv`, and `metric_trends.csv`.
