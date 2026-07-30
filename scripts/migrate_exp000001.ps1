param(
    [string]$LegacyRoot = "C:\PrimeAIExplorer\experiments\exp000001",
    [string]$NewRoot = "C:\PrimeAIExplorer\experiments\EXP-000001"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "EXP-000001 Migration Helper"
Write-Host "==========================="
Write-Host ""

if (-not (Test-Path $LegacyRoot)) {
    Write-Host "Legacy folder not found: $LegacyRoot"
    exit 0
}

New-Item -ItemType Directory -Path $NewRoot -Force | Out-Null

$Mappings = @(
    @{ Source = "responses"; Destination = "responses" },
    @{ Source = "results"; Destination = "results" },
    @{ Source = "reports"; Destination = "reports" }
)

foreach ($Map in $Mappings) {
    $SourcePath = Join-Path $LegacyRoot $Map.Source
    $DestinationPath = Join-Path $NewRoot $Map.Destination

    if (Test-Path $SourcePath) {
        New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null
        Copy-Item "$SourcePath\*" -Destination $DestinationPath -Recurse -Force
        Write-Host "Copied: $SourcePath -> $DestinationPath"
    }
}

Write-Host ""
Write-Host "Migration helper completed."
Write-Host "The legacy experiment was not deleted."
