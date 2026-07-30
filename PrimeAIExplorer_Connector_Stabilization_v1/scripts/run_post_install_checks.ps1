param(
    [string]$Root = "C:\PrimeAIExplorer"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $Root
try {
    py .\scripts\validate_connector_registry.py --root $Root

    py -m unittest `
        .\tests\test_connector_registry_stabilization.py `
        .\tests\test_execution_engine.py `
        -v

    py -m unittest discover `
        -s .\tests `
        -v
}
finally {
    Pop-Location
}
