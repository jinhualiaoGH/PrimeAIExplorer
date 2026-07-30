# PrimeAIExplorer v1.0.0-alpha8 Final Visualization Refresh

cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v1_0_0_alpha8_final

Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass

.\install.ps1
.\run_tests.ps1
.\run_demo.ps1

# Open the improved dashboard.
Start-Process .\demo_alpha8\dashboard.html

# Open representative figures.
Start-Process .\demo_alpha8\figures\reliability_diagram.svg
Start-Process .\demo_alpha8\figures\confusion_heatmap.svg
Start-Process .\demo_alpha8\figures\surprise_timeline.svg

# Verify imports and version.
.\.venv\Scripts\python.exe -c `
    "import primeaiexplorer; from primeaiexplorer.visualizations import SvgVisualizationEngine; print('Version:', primeaiexplorer.__version__); print('[PASS] Final Alpha8 visualization imports')"
