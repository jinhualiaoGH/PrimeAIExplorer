$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
py .\demo.py --provider all --trials 5
exit $LASTEXITCODE
