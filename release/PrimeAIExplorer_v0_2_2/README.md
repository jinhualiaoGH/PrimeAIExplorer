# PrimeAIExplorer v0.2.2

Native analysis of the canonical PrimeAIExplorer experiment format:

```text
dataset/cases.csv
pilot_xxx/responses.json
```

v0.2.2 also preserves support for legacy individual files named
`*.response.json` or `*_response.json`.

## New in v0.2.2

- Reads a pilot directory containing aggregate `responses.json` directly.
- Accepts common aggregate layouts: response arrays, `responses`/`records`/`items`/`results`, and CASE-ID-keyed mappings.
- Accepts nested response objects and JSON response strings.
- Adds `response-check` before analysis.
- Detects duplicates and unknown case IDs.
- Reports dataset coverage, window metrics, calibration, entropy, and explanation categories.
- Ignores mutable `current_response.json`; `responses.json` remains the canonical response ledger.

## Install

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_2_2
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

## Test and demo

```powershell
.\run_tests.ps1
.\run_demo.ps1
```

## Analyze the real pilot

```powershell
$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_2_2"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_001"
$Output = "$Root\experiments\exp000001\analysis_v022\pilot_001"

cd $Release

.\.venv\Scripts\paiexp.exe dataset-check `
    --dataset $Dataset

.\.venv\Scripts\paiexp.exe response-check `
    --responses $Pilot `
    --dataset $Dataset

.\.venv\Scripts\paiexp.exe analyze `
    --responses $Pilot `
    --dataset $Dataset `
    --output $Output `
    --model GPT-5.6-Thinking `
    --experiment-id EXP-000001 `
    --pilot-id pilot_001

.\.venv\Scripts\paiexp.exe verify `
    --analysis $Output

Start-Process "$Output\report.html"
```

For Pilot 002, change `$Pilot`, `$Output`, and `--pilot-id` to `pilot_002`.
