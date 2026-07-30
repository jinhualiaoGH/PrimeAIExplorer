$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Cli = Join-Path $Root ".venv\Scripts\paiexp.exe"
$Demo = Join-Path $Root "demo\exp000001"
$Dataset = Join-Path $Demo "dataset\cases.csv"
$Pilot = Join-Path $Demo "pilot_002"
$OutputA = Join-Path $Demo "analysis_v070\model_a"
$OutputB = Join-Path $Demo "analysis_v070\model_b"
$Comparison = Join-Path $Demo "comparison_v070"

if (-not (Test-Path $Python)) { throw "Python executable not found: $Python" }
if (-not (Test-Path $Cli)) { throw "PrimeAIExplorer CLI not found: $Cli" }

Push-Location $Root
try {
    Write-Host ""
    Write-Host "PrimeAIExplorer v1.0.0 RC3 release-candidate demonstration"
    Write-Host ("=" * 72)
    & $Python ".\test_performance_observatory_smoke.py"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python ".\test_behavior_observatory_smoke.py"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python ".\test_calibration_observatory_smoke.py"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python ".\test_distribution_observatory_smoke.py"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python ".\test_surprise_observatory_smoke.py"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python ".\test_alpha7_unified_dashboard_smoke.py"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python ".\test_alpha8_visualization_smoke.py"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host ""
    & $Cli doctor --json-output (Join-Path $Root "doctor_report.json")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Cli release-check --root $Root --json-output (Join-Path $Root "release_check.json")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host ""
    Write-Host "PrimeAIExplorer v0.7.3 compatibility demonstration"
    Write-Host ("=" * 72)
    Remove-Item $Demo -Recurse -Force -ErrorAction SilentlyContinue
    & $Python (Join-Path $Root "tools\make_demo.py")
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
}
finally {
    Pop-Location
}
