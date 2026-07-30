$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "PrimeAIExplorer v0.2 - Demo"
Write-Host "========================================================================"

$Python = ".\.venv\Scripts\python.exe"
$Cli = ".\.venv\Scripts\paiexp.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run .\install.ps1 first."
}

& $Python .\tools\make_demo.py --root .\demo\exp000001
& $Cli analyze `
    --responses .\demo\exp000001\pilot_001 `
    --truth .\demo\exp000001\truth.csv `
    --output .\demo\exp000001\analysis_v02 `
    --model demo-model `
    --experiment-id EXP-000001 `
    --pilot-id pilot_001

& $Cli verify --analysis .\demo\exp000001\analysis_v02

Write-Host ""
Write-Host "Open report:"
Write-Host "  $((Resolve-Path .\demo\exp000001\analysis_v02\report.html).Path)"
