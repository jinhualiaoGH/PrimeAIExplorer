param([string]$Destination = "C:\PrimeAIExplorer")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
function Invoke-Python {
    param([Parameter(Mandatory=$true)][string[]]$Arguments,[Parameter(Mandatory=$true)][string]$Label)
    Write-Host ""; Write-Host $Label
    & py @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE." }
}
$PackageRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path $Destination)) { throw "PrimeAIExplorer root does not exist: $Destination" }
$VersionFile = Join-Path $Destination "VERSION"
$CurrentVersion = (Get-Content $VersionFile -Raw).Trim()
if ($CurrentVersion -ne "1.2.2") { throw "PrimeAIExplorer v1.3 Phase A requires v1.2.2; found '$CurrentVersion'." }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $Destination "backups\v1.3.0_phase_a_before_install_$Stamp"
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
$RelativeFiles = @(
 "sequence_plugins\builtin\prime_value.py",
 "registries\sequence_plugin_registry.csv",
 "registries\sequence_plugin_registry.json",
 "experiments\EXP-000003\config\experiment.json",
 "scripts\dry_run_exp000003.py",
 "scripts\validate_v130_phase_a.py",
 "tests\test_prime_value_phase_a.py",
 "docs\PrimeValueSequencePlugin_Phase_A.md"
)
foreach ($Relative in $RelativeFiles) {
    $Source = Join-Path $PackageRoot $Relative
    $Target = Join-Path $Destination $Relative
    if (-not (Test-Path $Source)) { throw "Package file not found: $Source" }
    if (Test-Path $Target) {
        $Backup = Join-Path $BackupRoot $Relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $Backup) -Force | Out-Null
        Copy-Item $Target -Destination $Backup -Force
        Write-Host "[BACKUP] $Relative"
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $Target) -Force | Out-Null
    Copy-Item $Source -Destination $Target -Force
    Write-Host "[INSTALL] $Relative"
}
"1.3.0-phase-a" | Set-Content -Path $VersionFile -Encoding ascii
$ChangeLog = Join-Path $Destination "CHANGELOG.md"
@'

## 1.3.0-phase-a - Prime Value Plugin Contract

- Added production PrimeValueSequencePlugin configuration support.
- Added read-only PrimeNet partition discovery and source validation.
- Added EXP-000003 configuration and synchronized registries.
- Added EXP-000003 dry-run validation and focused tests.
- Explicitly deferred dataset construction and validation to Phase B.
'@ | Add-Content $ChangeLog
Push-Location $Destination
try {
    Invoke-Python -Label "Validating PrimeAIExplorer v1.3 Phase A..." -Arguments @(".\scripts\validate_v130_phase_a.py")
    Invoke-Python -Label "Running Prime Value Phase A tests..." -Arguments @("-m","unittest","discover","-s",".\tests","-p","test_prime_value_phase_a.py","-v")
    Invoke-Python -Label "Running complete regression suite..." -Arguments @("-m","unittest","discover","-s",".\tests","-v")
}
catch {
    Write-Host ""; Write-Host "PrimeAIExplorer v1.3 Phase A installation FAILED." -ForegroundColor Red
    Write-Host "Backup: $BackupRoot"; throw
}
finally { Pop-Location }
Write-Host ""; Write-Host "PrimeAIExplorer v1.3 Phase A installed successfully."
Write-Host "Backup: $BackupRoot"
Write-Host "Next read-only command: py .\scripts\dry_run_exp000003.py"
