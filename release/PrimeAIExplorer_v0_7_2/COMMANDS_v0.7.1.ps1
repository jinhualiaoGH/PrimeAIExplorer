$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v0_7_1"
$Experiment = "$Root\experiments\exp000001"
$Comparison = "$Experiment\comparison_v071"

cd $Release

# Discover all completed analyses under the experiment.
.\.venv\Scripts\paiexp.exe compare `
    --experiment-root "$Experiment" `
    --output "$Comparison"

# Verify and open when two or more analyses were discovered.
if (Test-Path "$Comparison\report.html") {
    .\.venv\Scripts\paiexp.exe compare-verify `
        --comparison "$Comparison"
    Start-Process "$Comparison\report.html"
}
