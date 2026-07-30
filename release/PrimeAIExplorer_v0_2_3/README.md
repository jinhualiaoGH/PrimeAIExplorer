# PrimeAIExplorer v0.2.3

PrimeAIExplorer v0.2.3 analyzes prime-gap prediction responses directly against the canonical `cases.csv` dataset.

## v0.2.3 improvements

- Reads UTF-8 and UTF-8-BOM response files.
- Reads standard JSON, JSON arrays, NDJSON/JSON Lines, and concatenated JSON objects.
- Assigns missing `case_id` values deterministically from `CASE-*.txt` prompt order.
- Auto-discovers prompts in the pilot root or nested `text` folders.
- Supports explicit `--prompts` when prompt files live elsewhere.
- Stores both the whole collection hash and a canonical per-entry hash.
- Normalizes numerical negative zero so entropy displays as `0.000`.
- Preserves v0.2.2 aggregate and individual response compatibility.

## Install

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_2_3
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

## Test and demo

```powershell
.\run_tests.ps1
.\run_demo.ps1
```

The demo deliberately uses the original Pilot 001-style format: a BOM-prefixed file containing consecutive JSON objects with no case IDs.

## Analyze Pilot 001 directly

No normalization directory is required:

```powershell
$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_2_3"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_001"
$Output = "$Root\experiments\exp000001\analysis_v023\pilot_001"

cd $Release

.\.venv\Scripts\paiexp.exe response-check `
    --responses "$Pilot" `
    --dataset "$Dataset"

.\.venv\Scripts\paiexp.exe analyze `
    --responses "$Pilot" `
    --dataset "$Dataset" `
    --output "$Output" `
    --model "GPT-5.6-Thinking" `
    --experiment-id "EXP-000001" `
    --pilot-id "pilot_001"

.\.venv\Scripts\paiexp.exe verify --analysis "$Output"
Start-Process "$Output\report.html"
```

## Analyze Pilot 002

The nested `pilot_002\text` directory is discovered automatically:

```powershell
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v023\pilot_002"

.\.venv\Scripts\paiexp.exe response-check `
    --responses "$Pilot" `
    --dataset "$Dataset"

.\.venv\Scripts\paiexp.exe analyze `
    --responses "$Pilot" `
    --dataset "$Dataset" `
    --output "$Output" `
    --model "GPT-5.6-Thinking" `
    --experiment-id "EXP-000001" `
    --pilot-id "pilot_002"
```

Use `--prompts <folder>` only when the prompt files are not under the response source directory.
