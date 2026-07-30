# PrimeAIExplorer v0.2.4

**Pilot Manager release** for partial, continuously growing response ledgers.

## New in v0.2.4

- Native support for preallocated ledgers containing `"response": null`.
- Pending entries are valid and excluded from scientific metrics.
- Separate ledger, completed, pending, pilot-completion, and dataset-coverage statistics.
- `pilot-status` command for collection progress and the next unfinished case.
- `next-case` command that prints the next prompt to collect.
- Progress cards in HTML and Markdown reports.
- Retains v0.2.3 support for BOM, concatenated JSON, NDJSON, nested response payloads, automatic case assignment, and per-entry hashing.

## Install

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_2_4
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

## Test

```powershell
.\run_tests.ps1
.\run_demo.ps1
```

## Real Pilot 002

```powershell
$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_2_4"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v024\pilot_002"
cd $Release

.\.venv\Scripts\paiexp.exe response-check --responses "$Pilot" --dataset "$Dataset"
.\.venv\Scripts\paiexp.exe pilot-status --responses "$Pilot" --dataset "$Dataset"
.\.venv\Scripts\paiexp.exe next-case --responses "$Pilot" --dataset "$Dataset"
.\.venv\Scripts\paiexp.exe analyze --responses "$Pilot" --dataset "$Dataset" --output "$Output" --model "GPT-5.6-Thinking" --experiment-id "EXP-000001" --pilot-id "pilot_002"
.\.venv\Scripts\paiexp.exe verify --analysis "$Output"
Start-Process "$Output\report.html"
```
