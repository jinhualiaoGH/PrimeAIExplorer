param(
    [string]$Destination = "C:\PrimeAIExplorer"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SourceRegistry = Join-Path $PackageRoot "connectors"
$TargetRegistry = Join-Path $Destination "connectors"
$TargetTests = Join-Path $Destination "tests"
$TargetScripts = Join-Path $Destination "scripts"

if (-not (Test-Path $Destination)) {
    throw "PrimeAIExplorer root does not exist: $Destination"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $Destination "backups\connector_registry_before_stabilization_$Stamp"

New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
New-Item -ItemType Directory -Path $TargetRegistry -Force | Out-Null
New-Item -ItemType Directory -Path $TargetTests -Force | Out-Null
New-Item -ItemType Directory -Path $TargetScripts -Force | Out-Null

foreach ($Name in @("connector_registry.csv", "connector_registry.json")) {
    $Existing = Join-Path $TargetRegistry $Name
    if (Test-Path $Existing) {
        Copy-Item $Existing -Destination $BackupRoot -Force
        Write-Host "[BACKUP] $Existing"
    }

    Copy-Item (Join-Path $SourceRegistry $Name) -Destination $Existing -Force
    Write-Host "[INSTALL] $Existing"
}

Copy-Item `
    (Join-Path $PackageRoot "scripts\validate_connector_registry.py") `
    -Destination $TargetScripts `
    -Force

Copy-Item `
    (Join-Path $PackageRoot "tests\test_connector_registry_stabilization.py") `
    -Destination $TargetTests `
    -Force

Write-Host ""
Write-Host "Validating connector registry..."
Push-Location $Destination
try {
    py .\scripts\validate_connector_registry.py --root $Destination

    Write-Host ""
    Write-Host "Running focused registry tests..."
    py -m unittest `
        .\tests\test_connector_registry_stabilization.py `
        .\tests\test_execution_engine.py `
        -v
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Connector stabilization installed successfully."
Write-Host "Backup: $BackupRoot"
