$ErrorActionPreference = "Stop"

$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_2_3"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_001"
$Output = "$Root\experiments\exp000001\analysis_v023\pilot_001"

cd $Release

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
.\run_tests.ps1
.\run_demo.ps1

.\.venv\Scripts\paiexp.exe dataset-check `
    --dataset "$Dataset"

.\.venv\Scripts\paiexp.exe response-check `
    --responses "$Pilot" `
    --dataset "$Dataset"

Remove-Item "$Output" -Recurse -Force -ErrorAction SilentlyContinue

.\.venv\Scripts\paiexp.exe analyze `
    --responses "$Pilot" `
    --dataset "$Dataset" `
    --output "$Output" `
    --model "GPT-5.6-Thinking" `
    --experiment-id "EXP-000001" `
    --pilot-id "pilot_001"

.\.venv\Scripts\paiexp.exe verify `
    --analysis "$Output"

Start-Process "$Output\report.html"
