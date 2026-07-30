param(
    [string]$Destination = "C:\PrimeAIExplorer"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path $Destination)) {
    throw "PrimeAIExplorer root does not exist: $Destination"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $Destination "backups\v1.1_before_install_$Stamp"
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$RelativeFiles = @(
    "plugins\left_twin.py",
    "plugins\__init__.py",
    "core\baselines.py",
    "core\run_summary.py",
    "experiments\EXP-000002\config\experiment.json",
    "run_experiment.py",
    "tests\test_exp000002_v11.py",
    "scripts\validate_v11.py",
    "docs\EXP-000002_v1.1.md"
)

foreach ($Relative in $RelativeFiles) {
    $Source = Join-Path $PackageRoot $Relative
    $Target = Join-Path $Destination $Relative

    if (-not (Test-Path $Source)) {
        throw "Package file missing: $Source"
    }

    if (Test-Path $Target) {
        $Backup = Join-Path $BackupRoot $Relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $Backup) -Force |
            Out-Null
        Copy-Item $Target -Destination $Backup -Force
        Write-Host "[BACKUP] $Relative"
    }

    New-Item -ItemType Directory -Path (Split-Path -Parent $Target) -Force |
        Out-Null
    Copy-Item $Source -Destination $Target -Force
    Write-Host "[INSTALL] $Relative"
}

$VersionPath = Join-Path $Destination "VERSION"
if (Test-Path $VersionPath) {
    Copy-Item $VersionPath -Destination (Join-Path $BackupRoot "VERSION") -Force
}
"1.1.0" | Set-Content $VersionPath -Encoding ascii

$ChangeLog = Join-Path $Destination "CHANGELOG.md"
@'

## 1.1.0 - EXP-000002 Left Twin Prime Benchmark

- Hardened the `left_twin` sequence plugin.
- Added atomic uint64 dataset generation and SHA-256 metadata.
- Added dataset validation.
- Added deterministic baseline generation.
- Added score summary generation.
- Added EXP-000002 synthetic end-to-end tests.
- Added the v1.1 pipeline commands.
'@ | Add-Content $ChangeLog

Push-Location $Destination
try {
    py .\scripts\validate_v11.py

    py -m unittest discover `
        -s .\tests `
        -p "test_exp000002_v11.py" `
        -v

    py -m unittest discover `
        -s .\tests `
        -v
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "PrimeAIExplorer v1.1 installed successfully."
Write-Host "Backup: $BackupRoot"
