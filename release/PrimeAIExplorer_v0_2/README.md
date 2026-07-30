# PrimeAIExplorer v0.2

PrimeAIExplorer v0.2 adds a reproducible response-analysis pipeline to the v0.1 pilot workflow.

## Main capabilities

- strict JSON response validation
- exact-match accuracy and error summaries
- confidence calibration, Brier score, and ECE
- prediction entropy and response diversity
- explanation phrase/style analysis
- per-run manifests with SHA-256 hashes
- CSV, Markdown, JSON, and standalone HTML reports
- deterministic demo data and unit tests

## Expected experiment layout

```text
experiments/exp000001/
  pilot_001/
    CASE-W004-0001.txt
    CASE-W004-0001.response.json
    CASE-W008-0001.txt
    CASE-W008-0001.response.json
  truth.csv
```

`truth.csv` must contain:

```csv
case_id,actual_gap
CASE-W004-0001,6
CASE-W008-0001,8
```

Response files use the existing contract:

```json
{
  "prediction": 6,
  "confidence": 72,
  "explanation": "Six is frequent in the local sequence."
}
```

## Quick start

From the package directory in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
.\run_demo.ps1
```

Analyze a real pilot:

```powershell
paiexp analyze `
    --responses .\experiments\exp000001\pilot_001 `
    --truth .\experiments\exp000001\truth.csv `
    --output .\experiments\exp000001\analysis_v02 `
    --model GPT-5.6-Thinking `
    --experiment-id EXP-000001 `
    --pilot-id pilot_001
```

The output folder contains `records.csv`, `summary.json`, `manifest.json`, `report.md`, and `report.html`.
