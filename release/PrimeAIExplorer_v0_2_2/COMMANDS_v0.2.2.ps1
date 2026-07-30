# PrimeAIExplorer v0.2.2 command sheet

$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_2_2"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"

cd $Release
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\install.ps1
.\run_tests.ps1
.\run_demo.ps1

# Pilot 001
$Pilot = "$Root\experiments\exp000001\pilot_001"
$Output = "$Root\experiments\exp000001\analysis_v022\pilot_001"

.\.venv\Scripts\paiexp.exe dataset-check --dataset $Dataset
.\.venv\Scripts\paiexp.exe response-check --responses $Pilot --dataset $Dataset
.\.venv\Scripts\paiexp.exe analyze `
    --responses $Pilot `
    --dataset $Dataset `
    --output $Output `
    --model GPT-5.6-Thinking `
    --experiment-id EXP-000001 `
    --pilot-id pilot_001
.\.venv\Scripts\paiexp.exe verify --analysis $Output
Start-Process "$Output\report.html"

# Pilot 002
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v022\pilot_002"

.\.venv\Scripts\paiexp.exe response-check --responses $Pilot --dataset $Dataset
.\.venv\Scripts\paiexp.exe analyze `
    --responses $Pilot `
    --dataset $Dataset `
    --output $Output `
    --model GPT-5.6-Thinking `
    --experiment-id EXP-000001 `
    --pilot-id pilot_002
.\.venv\Scripts\paiexp.exe verify --analysis $Output
Start-Process "$Output\report.html"
