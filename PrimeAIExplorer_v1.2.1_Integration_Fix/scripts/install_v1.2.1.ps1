param(
    [string]$Destination = "C:\PrimeAIExplorer"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    Write-Host ""
    Write-Host $Label
    & py @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

$PackageRoot = Split-Path -Parent (
    Split-Path -Parent $MyInvocation.MyCommand.Path
)

if (-not (Test-Path $Destination)) {
    throw "PrimeAIExplorer root does not exist: $Destination"
}

$VersionFile = Join-Path $Destination "VERSION"
if (-not (Test-Path $VersionFile)) {
    throw "VERSION file not found: $VersionFile"
}

$CurrentVersion = (Get-Content $VersionFile -Raw).Trim()
if ($CurrentVersion -notin @("1.2.0", "1.1.1")) {
    throw "v1.2.1 requires v1.2.0 or v1.1.1; found '$CurrentVersion'."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path `
    $Destination `
    "backups\v1.2.1_before_install_$Stamp"
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$RelativeFiles = @(
    "sequence_plugins\builtin\__init__.py",
    "sequence_plugins\builtin\left_twin.py",
    "scripts\list_sequence_plugins.py",
    "scripts\validate_v121.py",
    "tests\test_sequence_framework_v121.py",
    "docs\v1.2.1_Integration_Fix.md"
)

foreach ($Relative in $RelativeFiles) {
    $Source = Join-Path $PackageRoot $Relative
    $Target = Join-Path $Destination $Relative

    if (-not (Test-Path $Source)) {
        throw "Package file not found: $Source"
    }

    if (Test-Path $Target) {
        $Backup = Join-Path $BackupRoot $Relative
        New-Item `
            -ItemType Directory `
            -Path (Split-Path -Parent $Backup) `
            -Force |
            Out-Null
        Copy-Item $Target -Destination $Backup -Force
        Write-Host "[BACKUP] $Relative"
    }

    New-Item `
        -ItemType Directory `
        -Path (Split-Path -Parent $Target) `
        -Force |
        Out-Null
    Copy-Item $Source -Destination $Target -Force
    Write-Host "[INSTALL] $Relative"
}

# Preserve the v1.2.0 test for regression evidence; v1.2.1 adds a new test file.
"1.2.1" | Set-Content -Path $VersionFile -Encoding ascii

$ChangeLog = Join-Path $Destination "CHANGELOG.md"
@'

## 1.2.1 - Sequence Framework Integration Fix

- Corrected project-root imports for helper scripts.
- Rebuilt the Left Twin adapter against the verified v1.1.1 class API.
- Removed eager built-in plugin imports.
- Added explicit native exit-code checks to the installer.
- Added adapter integration regression tests.
'@ | Add-Content $ChangeLog

Push-Location $Destination
try {
    Invoke-Python `
        -Label "Validating PrimeAIExplorer v1.2.1..." `
        -Arguments @(".\scripts\validate_v121.py")

    Invoke-Python `
        -Label "Listing sequence plugins..." `
        -Arguments @(".\scripts\list_sequence_plugins.py")

    Invoke-Python `
        -Label "Running v1.2.0 framework regression tests..." `
        -Arguments @(
            "-m", "unittest", "discover",
            "-s", ".\tests",
            "-p", "test_sequence_framework_v120.py",
            "-v"
        )

    Invoke-Python `
        -Label "Running v1.2.1 integration tests..." `
        -Arguments @(
            "-m", "unittest", "discover",
            "-s", ".\tests",
            "-p", "test_sequence_framework_v121.py",
            "-v"
        )

    Invoke-Python `
        -Label "Running complete regression suite..." `
        -Arguments @(
            "-m", "unittest", "discover",
            "-s", ".\tests",
            "-v"
        )
}
catch {
    Write-Host ""
    Write-Host "PrimeAIExplorer v1.2.1 installation FAILED." -ForegroundColor Red
    Write-Host "Backup: $BackupRoot"
    throw
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "PrimeAIExplorer v1.2.1 installed successfully."
Write-Host "Backup: $BackupRoot"
