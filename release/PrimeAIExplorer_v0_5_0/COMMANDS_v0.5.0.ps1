$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_5_0"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v050\pilot_002"
cd $Release
.\.venv\Scripts\paiexp.exe analyze --responses "$Pilot" --dataset "$Dataset" --output "$Output" --model "GPT-5.6 Thinking" --experiment-id "EXP-000001" --pilot-id "pilot_002"
.\.venv\Scripts\paiexp.exe verify --analysis "$Output"
Start-Process "$Output\report.html"
