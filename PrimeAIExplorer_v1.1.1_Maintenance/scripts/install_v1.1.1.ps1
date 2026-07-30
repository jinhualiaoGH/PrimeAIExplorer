param(
    [string]$Destination = "C:\PrimeAIExplorer"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$PackageRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not (Test-Path $Destination)) {
    throw "PrimeAIExplorer root does not exist: $Destination"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $Destination "backups\v1.1.1_before_install_$Stamp"

New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Destination "scripts") -Force |
    Out-Null
New-Item -ItemType Directory -Path (Join-Path $Destination "tests") -Force |
    Out-Null
New-Item -ItemType Directory -Path (Join-Path $Destination "docs") -Force |
    Out-Null

$FilesToInstall = @(
    "scripts\validate_v111.py",
    "tests\test_v111_compatibility.py",
    "docs\v1.1.1_Maintenance.md"
)

foreach ($Relative in $FilesToInstall) {
    $Source = Join-Path $PackageRoot $Relative
    $Target = Join-Path $Destination $Relative

    if (-not (Test-Path $Source)) {
        throw "Package file not found: $Source"
    }

    if (Test-Path $Target) {
        $Backup = Join-Path $BackupRoot $Relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $Backup) -Force |
            Out-Null
        Copy-Item $Target -Destination $Backup -Force
        Write-Host "[BACKUP] $Relative"
    }

    Copy-Item $Source -Destination $Target -Force
    Write-Host "[INSTALL] $Relative"
}

Write-Host ""
Write-Host "Applying maintenance patch..."

py (Join-Path $PackageRoot "patches\apply_v111.py") `
    --root $Destination `
    --backup-root $BackupRoot

"1.1.1" |
    Set-Content `
        -Path (Join-Path $Destination "VERSION") `
        -Encoding ascii

$ChangeLog = Join-Path $Destination "CHANGELOG.md"
@'

## 1.1.1 - Maintenance Release

- Restored `is_probable_prime_64` as a backward-compatible alias.
- Corrected the synthetic EXP-000002 fixture.
- Added permanent compatibility regression tests.
- Made installer success contingent on all validations and tests passing.
'@ | Add-Content $ChangeLog

Push-Location $Destination
try {
    Write-Host ""
    Write-Host "Validating v1.1.1..."
    py .\scripts\validate_v111.py

    Write-Host ""
    Write-Host "Running focused maintenance tests..."
    py -m unittest discover `
        -s .\tests `
        -p "test_v111_compatibility.py" `
        -v

    py -m unittest discover `
        -s .\tests `
        -p "test_exp000002_v11.py" `
        -v

    Write-Host ""
    Write-Host "Running complete regression suite..."
    py -m unittest discover `
        -s .\tests `
        -v
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "PrimeAIExplorer v1.1.1 installed successfully."
Write-Host "Backup: $BackupRoot"
