$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host ""
Write-Host "PrimeAIExplorer v1.0.0-alpha1 - Install"
Write-Host ("=" * 72)

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

try {
    .\.venv\Scripts\python.exe -m pip install -e ".[workspace]"
    Write-Host "[PASS] Optional workspace command history enabled."
}
catch {
    Write-Warning "Optional prompt-toolkit installation failed; using standard input fallback."
    .\.venv\Scripts\python.exe -m pip install -e .
}

Write-Host ""
Write-Host "Installation complete."
Write-Host "CLI: .\.venv\Scripts\paiexp.exe --help"
