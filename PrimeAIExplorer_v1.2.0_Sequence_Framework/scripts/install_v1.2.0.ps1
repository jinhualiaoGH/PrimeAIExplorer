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

$VersionFile = Join-Path $Destination "VERSION"
if (-not (Test-Path $VersionFile)) {
    throw "VERSION file not found: $VersionFile"
}

$CurrentVersion = (Get-Content $VersionFile -Raw).Trim()
if ($CurrentVersion -ne "1.1.1") {
    throw "PrimeAIExplorer v1.2.0 requires v1.1.1; found '$CurrentVersion'."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $Destination "backups\v1.2.0_before_install_$Stamp"
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$Directories = @(
    "sequence_plugins",
    "registries",
    "scripts",
    "tests",
    "docs"
)

foreach ($Directory in $Directories) {
    New-Item `
        -ItemType Directory `
        -Path (Join-Path $Destination $Directory) `
        -Force |
        Out-Null
}

$RelativeFiles = @(
    "sequence_plugins\__init__.py",
    "sequence_plugins\base.py",
    "sequence_plugins\registry.py",
    "sequence_plugins\loader.py",
    "sequence_plugins\builtin\__init__.py",
    "sequence_plugins\builtin\numpy_file.py",
    "sequence_plugins\builtin\integer_sequence.py",
    "sequence_plugins\builtin\left_twin.py",
    "sequence_plugins\builtin\prime_gap.py",
    "sequence_plugins\builtin\prime_square.py",
    "sequence_plugins\builtin\prime_value.py",
    "registries\sequence_plugin_registry.csv",
    "registries\sequence_plugin_registry.json",
    "scripts\list_sequence_plugins.py",
    "scripts\validate_v120.py",
    "tests\test_sequence_framework_v120.py",
    "docs\Sequence_Plugin_Framework_v1.2.md",
    "docs\v1.2.0_Release_Notes.md"
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

"1.2.0" |
    Set-Content `
        -Path $VersionFile `
        -Encoding ascii

$ChangeLog = Join-Path $Destination "CHANGELOG.md"
@'

## 1.2.0 - Sequence Framework

- Added the generic SequencePlugin contract.
- Added declarative CSV and JSON plugin registries.
- Added dynamic plugin loading.
- Added a compatibility-preserving Left Twin adapter.
- Added Integer Sequence, Prime Value, Prime Gap, and Prime Square plugins.
- Added generic case, prompt, and prediction-evaluation support.
- Added v1.2 validation and regression tests.
'@ | Add-Content $ChangeLog

Push-Location $Destination
try {
    Write-Host ""
    Write-Host "Validating PrimeAIExplorer v1.2.0..."
    py .\scripts\validate_v120.py

    Write-Host ""
    Write-Host "Listing sequence plugins..."
    py .\scripts\list_sequence_plugins.py

    Write-Host ""
    Write-Host "Running v1.2 sequence-framework tests..."
    py -m unittest discover `
        -s .\tests `
        -p "test_sequence_framework_v120.py" `
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
Write-Host "PrimeAIExplorer v1.2.0 installed successfully."
Write-Host "Backup: $BackupRoot"
