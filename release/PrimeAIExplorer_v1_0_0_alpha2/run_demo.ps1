$ErrorActionPreference = "Stop"

$Python = Join-Path `
    $PSScriptRoot `
    ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Python executable not found: $Python"
}

Push-Location $PSScriptRoot

try {
    # Existing inherited demonstration commands remain here.

    Write-Host ""
    Write-Host "PrimeAIExplorer v1.0.0-alpha2 Performance Observatory smoke test"

    & $Python `
        ".\test_performance_observatory_smoke.py"
}
finally {
    Pop-Location
}
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cli = Join-Path $Root ".venv\Scripts\paiexp.exe"
$Demo = Join-Path $Root "demo\exp000001"
$Dataset = Join-Path $Demo "dataset\cases.csv"
$Pilot = Join-Path $Demo "pilot_002"
$OutputA = Join-Path $Demo "analysis_v070\model_a"
$OutputB = Join-Path $Demo "analysis_v070\model_b"
$Comparison = Join-Path $Demo "comparison_v070"

Write-Host ""
Write-Host "PrimeAIExplorer v0.7.1 - Comparative Observatory Demo"
Write-Host ("=" * 72)

Remove-Item $Demo -Recurse -Force -ErrorAction SilentlyContinue
& (Join-Path $Root ".venv\Scripts\python.exe") (Join-Path $Root "tools\make_demo.py")
& $Cli dataset-check --dataset $Dataset
& $Cli workspace --responses $Pilot --dataset $Dataset --analysis-output $OutputA --model "GPT-5.6 Thinking" --experiment-id "EXP-000001" --pilot-id "pilot_002_a" --commands "progress,prompt,validate,commit,history,refresh,exit"
& $Cli verify --analysis $OutputA
& $Cli analyze --responses $Pilot --dataset $Dataset --output $OutputB --model "Comparison Model" --experiment-id "EXP-000001" --pilot-id "pilot_002_b"
& $Cli verify --analysis $OutputB
& $Cli compare --analysis $OutputA --label "GPT-5.6 Thinking" --analysis $OutputB --label "Comparison Model" --output $Comparison
& $Cli compare-verify --comparison $Comparison

Write-Host ""
Write-Host "Open comparative report:"
Write-Host "  $Comparison\report.html"

