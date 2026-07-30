$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Cli = Join-Path $Root ".venv\Scripts\paiexp.exe"

Write-Host ""
Write-Host "PrimeAIExplorer v0.2.2 - Aggregate Response Demo"
Write-Host ("=" * 72)

& $Python (Join-Path $Root "tools\make_demo.py")
$Demo = Join-Path $Root "demo\exp000001"
$Dataset = Join-Path $Demo "dataset\cases.csv"
$Pilot = Join-Path $Demo "pilot_001"
$Analysis = Join-Path $Demo "analysis_v022"

& $Cli dataset-check --dataset $Dataset
& $Cli response-check --responses $Pilot --dataset $Dataset
& $Cli analyze --responses $Pilot --dataset $Dataset --output $Analysis --model "demo-model" --experiment-id "EXP-000001" --pilot-id "pilot_001"
& $Cli verify --analysis $Analysis

Write-Host ""
Write-Host "Open report:"
Write-Host "  $(Join-Path $Analysis 'report.html')"
