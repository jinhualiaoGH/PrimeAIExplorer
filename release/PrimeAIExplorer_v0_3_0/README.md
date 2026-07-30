# PrimeAIExplorer v0.3.0

PrimeAIExplorer v0.3.0 is the **Interactive Workspace** release. It keeps every validated v0.2.6 command and adds one research-cockpit command:

```text
paiexp workspace
```

The workspace combines collection progress, next-prompt review, editor launch, response validation, atomic commit, history, dashboard refresh, and report opening.

## Install

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_3_0
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

## Test

```powershell
.\run_tests.ps1
.\run_demo.ps1
```

## Start the real workspace

```powershell
$Root = "C:\PrimeAIExplorer"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v030\pilot_002"

.\.venv\Scripts\paiexp.exe workspace `
    --responses "$Pilot" `
    --dataset "$Dataset" `
    --analysis-output "$Output" `
    --model "GPT-5.6 Thinking" `
    --experiment-id "EXP-000001" `
    --pilot-id "pilot_002"
```

## Workspace menu

```text
1) Show progress
2) Show next prompt
3) Open response editor
4) Validate current response
5) Commit response
6) Show response history
7) Refresh analysis
8) Open HTML report
9) Exit
```

A successful commit refreshes the dashboard automatically. Disable that behavior with `--no-auto-refresh`.

For automation and testing, use scripted actions:

```powershell
.\.venv\Scripts\paiexp.exe workspace `
    --responses "$Pilot" `
    --dataset "$Dataset" `
    --analysis-output "$Output" `
    --commands "progress,prompt,history,exit"
```
