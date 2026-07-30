# 1. Extract PrimeAIExplorer_v0_2.zip into C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_2
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_2

# 2. Install
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1

# 3. Confirm CLI
.\.venv\Scripts\paiexp.exe --version
.\.venv\Scripts\paiexp.exe --help

# 4. Run tests and demo
.\run_tests.ps1
.\run_demo.ps1

# 5. Analyze the existing EXP-000001 pilot
.\.venv\Scripts\paiexp.exe analyze `
    --responses C:\PrimeAIExplorer\experiments\exp000001\pilot_001 `
    --truth C:\PrimeAIExplorer\experiments\exp000001\truth.csv `
    --output C:\PrimeAIExplorer\experiments\exp000001\analysis_v02 `
    --model GPT-5.6-Thinking `
    --experiment-id EXP-000001 `
    --pilot-id pilot_001

# 6. Verify generated artifacts
.\.venv\Scripts\paiexp.exe verify `
    --analysis C:\PrimeAIExplorer\experiments\exp000001\analysis_v02

# 7. Open the dashboard
Start-Process C:\PrimeAIExplorer\experiments\exp000001\analysis_v02\report.html
