$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_2_5"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v025\pilot_002"

cd $Release

.\.venv\Scripts\paiexp.exe pilot-status --responses "$Pilot" --dataset "$Dataset"
.\.venv\Scripts\paiexp.exe next-case --responses "$Pilot" --dataset "$Dataset"
.\.venv\Scripts\paiexp.exe collect --responses "$Pilot" --dataset "$Dataset" --model "GPT-5.6 Thinking"
.\.venv\Scripts\paiexp.exe analyze --responses "$Pilot" --dataset "$Dataset" --output "$Output" --model "GPT-5.6-Thinking" --experiment-id "EXP-000001" --pilot-id "pilot_002"
.\.venv\Scripts\paiexp.exe verify --analysis "$Output"
Start-Process "$Output\report.html"
