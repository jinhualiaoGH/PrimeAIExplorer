$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_2_6"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v026\pilot_002"

cd $Release

.\.venv\Scripts\paiexp.exe progress --responses "$Pilot" --dataset "$Dataset"
.\.venv\Scripts\paiexp.exe history --responses "$Pilot" --dataset "$Dataset"
.\.venv\Scripts\paiexp.exe resume --responses "$Pilot" --dataset "$Dataset" --open-editor

.\.venv\Scripts\paiexp.exe collect `
    --responses "$Pilot" `
    --dataset "$Dataset" `
    --model "GPT-5.6 Thinking" `
    --refresh-analysis `
    --analysis-output "$Output" `
    --experiment-id "EXP-000001" `
    --pilot-id "pilot_002"

.\.venv\Scripts\paiexp.exe verify --analysis "$Output"
Start-Process "$Output\report.html"
