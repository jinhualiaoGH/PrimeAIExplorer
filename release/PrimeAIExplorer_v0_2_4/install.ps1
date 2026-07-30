$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host ""
Write-Host "PrimeAIExplorer v0.2.4 - Install"
Write-Host ("=" * 72)

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -e .

Write-Host ""
Write-Host "Installation complete."
Write-Host "CLI: .\.venv\Scripts\paiexp.exe --help"
