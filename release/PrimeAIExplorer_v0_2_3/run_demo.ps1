$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cli = Join-Path $Root ".venv\Scripts\paiexp.exe"
$Demo = Join-Path $Root "demo\exp000001"
$Dataset = Join-Path $Demo "dataset\cases.csv"
$Pilot = Join-Path $Demo "pilot_001"
$Output = Join-Path $Demo "analysis_v023"

Write-Host ""
Write-Host "PrimeAIExplorer v0.2.3 - Native Legacy Response Demo"
Write-Host ("=" * 72)

Remove-Item $Demo -Recurse -Force -ErrorAction SilentlyContinue
& (Join-Path $Root ".venv\Scripts\python.exe") (Join-Path $Root "tools\make_demo.py")
& $Cli dataset-check --dataset $Dataset
& $Cli response-check --responses $Pilot --dataset $Dataset
& $Cli analyze --responses $Pilot --dataset $Dataset --output $Output --model "GPT-5.6-Thinking" --experiment-id "EXP-000001" --pilot-id "pilot_001"
& $Cli verify --analysis $Output

Write-Host ""
Write-Host "Open report:"
Write-Host "  $Output\report.html"
