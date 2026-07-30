# PrimeAIExplorer v0.2.6

PrimeAIExplorer v0.2.6 is the **Collection Workflow** release. It builds on the atomic v0.2.5 collector with concise progress, response history, one-command resume, and optional automatic dashboard refresh.

## New commands

- `progress`: progress bar plus completed/total counts for each observation window.
- `history`: compact table of collected predictions, truths, confidence, and correctness.
- `resume`: shows collection state, the next prompt, and the working response file; `--open-editor` opens it on Windows.
- `collect --refresh-analysis`: commits a response and immediately rebuilds the scientific report.

## Install

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_2_6
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

## Test and demo

```powershell
.\run_tests.ps1
.\run_demo.ps1
```

## Recommended workflow

```powershell
.\.venv\Scripts\paiexp.exe progress --responses $Pilot --dataset $Dataset
.\.venv\Scripts\paiexp.exe resume --responses $Pilot --dataset $Dataset --open-editor
.\.venv\Scripts\paiexp.exe collect --responses $Pilot --dataset $Dataset --model "GPT-5.6 Thinking" --refresh-analysis --analysis-output $Output --experiment-id EXP-000001 --pilot-id pilot_002
.\.venv\Scripts\paiexp.exe history --responses $Pilot --dataset $Dataset
```
