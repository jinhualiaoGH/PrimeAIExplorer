$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "PrimeAIExplorer v0.2 - Install"
Write-Host "========================================================================"

if (-not (Test-Path ".\.venv")) {
    py -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -e .

Write-Host ""
Write-Host "Installation complete."
Write-Host "CLI: .\.venv\Scripts\paiexp.exe --help"
