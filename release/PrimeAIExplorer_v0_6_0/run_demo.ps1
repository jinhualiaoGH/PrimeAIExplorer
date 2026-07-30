$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cli = Join-Path $Root ".venv\Scripts\paiexp.exe"
$Demo = Join-Path $Root "demo\exp000001"
$Dataset = Join-Path $Demo "dataset\cases.csv"
$Pilot = Join-Path $Demo "pilot_002"
$Output = Join-Path $Demo "analysis_v060"

Write-Host ""
Write-Host "PrimeAIExplorer v0.6.0 - Interactive Workspace Demo"
Write-Host ("=" * 72)

Remove-Item $Demo -Recurse -Force -ErrorAction SilentlyContinue
& (Join-Path $Root ".venv\Scripts\python.exe") (Join-Path $Root "tools\make_demo.py")
& $Cli dataset-check --dataset $Dataset
& $Cli workspace --responses $Pilot --dataset $Dataset --analysis-output $Output --model "GPT-5.6 Thinking" --experiment-id "EXP-000001" --pilot-id "pilot_002" --commands "progress,prompt,validate,commit,history,refresh,exit"
& $Cli verify --analysis $Output

Write-Host ""
Write-Host "Open report:"
Write-Host "  $Output\report.html"
