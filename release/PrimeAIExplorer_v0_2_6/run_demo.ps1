$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cli = Join-Path $Root ".venv\Scripts\paiexp.exe"
$Demo = Join-Path $Root "demo\exp000001"
$Dataset = Join-Path $Demo "dataset\cases.csv"
$Pilot = Join-Path $Demo "pilot_002"
$Output = Join-Path $Demo "analysis_v026"

Write-Host ""
Write-Host "PrimeAIExplorer v0.2.6 - Collection Workflow Demo"
Write-Host ("=" * 72)

Remove-Item $Demo -Recurse -Force -ErrorAction SilentlyContinue
& (Join-Path $Root ".venv\Scripts\python.exe") (Join-Path $Root "tools\make_demo.py")
& $Cli dataset-check --dataset $Dataset
& $Cli progress --responses $Pilot --dataset $Dataset
& $Cli history --responses $Pilot --dataset $Dataset
& $Cli resume --responses $Pilot --dataset $Dataset
& $Cli collect --responses $Pilot --dataset $Dataset --model "GPT-5.6 Thinking" --refresh-analysis --analysis-output $Output --experiment-id "EXP-000001" --pilot-id "pilot_002"
& $Cli verify --analysis $Output

Write-Host ""
Write-Host "Open report:"
Write-Host "  $Output\report.html"
