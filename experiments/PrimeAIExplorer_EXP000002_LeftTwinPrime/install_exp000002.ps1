param(
    [string]$PrimeAIExplorerRoot = "C:\PrimeAIExplorer"
)

$ErrorActionPreference = "Stop"

$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Destination = Join-Path $PrimeAIExplorerRoot "experiments\exp000002_left_twin_prime"

Write-Host ""
Write-Host "PrimeAIExplorer EXP-000002 Installer"
Write-Host "===================================="
Write-Host "Source:      $SourceRoot"
Write-Host "Destination: $Destination"
Write-Host ""

New-Item -ItemType Directory -Path $Destination -Force | Out-Null

Get-ChildItem -Path $SourceRoot -Force |
    Where-Object { $_.Name -ne "install_exp000002.ps1" } |
    Copy-Item -Destination $Destination -Recurse -Force

Write-Host "Installed EXP-000002."
Write-Host ""
Write-Host "Next:"
Write-Host "  cd $PrimeAIExplorerRoot"
Write-Host "  notepad .\experiments\exp000002_left_twin_prime\config\experiment_config.json"
