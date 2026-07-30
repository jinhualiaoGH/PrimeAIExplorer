$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_7_0"
$AnalysisA = "$Root\experiments\exp000001\analysis_v060\pilot_002"
$AnalysisB = "$Root\experiments\exp000001\analysis_model_b\pilot_002"
$Comparison = "$Root\experiments\exp000001\comparison_v070"

cd $Release

.\.venv\Scripts\paiexp.exe compare `
    --analysis "$AnalysisA" `
    --label "GPT-5.6 Thinking" `
    --analysis "$AnalysisB" `
    --label "Model B" `
    --output "$Comparison"

.\.venv\Scripts\paiexp.exe compare-verify `
    --comparison "$Comparison"

Start-Process "$Comparison\report.html"
