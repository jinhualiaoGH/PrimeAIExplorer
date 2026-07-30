$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_3_0"
$Dataset = "$Root\experiments\exp000001\dataset\cases.csv"
$Pilot = "$Root\experiments\exp000001\pilot_002"
$Output = "$Root\experiments\exp000001\analysis_v030\pilot_002"

cd $Release

# Interactive research cockpit
.\.venv\Scripts\paiexp.exe workspace `
    --responses "$Pilot" `
    --dataset "$Dataset" `
    --analysis-output "$Output" `
    --model "GPT-5.6 Thinking" `
    --experiment-id "EXP-000001" `
    --pilot-id "pilot_002"

# Scripted, non-interactive example
.\.venv\Scripts\paiexp.exe workspace `
    --responses "$Pilot" `
    --dataset "$Dataset" `
    --analysis-output "$Output" `
    --model "GPT-5.6 Thinking" `
    --experiment-id "EXP-000001" `
    --pilot-id "pilot_002" `
    --commands "progress,prompt,history,exit"
