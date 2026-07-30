param(
    [string]$ExperimentRoot = "C:\PrimeAIExplorer\experiments\exp000002_left_twin_prime"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "EXP-000002 Smoke Test"
Write-Host "====================="
Write-Host ""

py -m compileall "$ExperimentRoot\src"

Write-Host ""
Write-Host "Compilation passed."
Write-Host ""
Write-Host "Run source validation next:"
Write-Host "py `"$ExperimentRoot\src\validate_sources.py`" --config `"$ExperimentRoot\config\experiment_config.json`""
