param(
    [string]$Destination = "C:\PrimeAIExplorer"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "PrimeAIExplorer Architecture Specification v1.0 Installer"
Write-Host "========================================================="
Write-Host "Package:     $PackageRoot"
Write-Host "Destination: $Destination"
Write-Host ""

foreach ($Directory in @("docs", "schemas", "templates")) {
    $Source = Join-Path $PackageRoot $Directory
    $Target = Join-Path $Destination $Directory

    New-Item -ItemType Directory -Path $Target -Force | Out-Null
    Copy-Item "$Source\*" -Destination $Target -Recurse -Force
    Write-Host "[INSTALLED] $Directory"
}

$ValidatorSource = Join-Path $PackageRoot "scripts\validate_architecture_spec.py"
$ScriptsTarget = Join-Path $Destination "scripts"
New-Item -ItemType Directory -Path $ScriptsTarget -Force | Out-Null
Copy-Item $ValidatorSource -Destination $ScriptsTarget -Force

Write-Host ""
Write-Host "Running validation..."
cd $Destination
py .\scripts\validate_architecture_spec.py

Write-Host ""
Write-Host "Architecture specification installed successfully."
