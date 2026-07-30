cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v1_0_0_alpha4
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
.\run_tests.ps1
.\run_demo.ps1
.\.venv\Scripts\python.exe .\test_calibration_observatory_smoke.py
.\.venv\Scripts\python.exe .\test_distribution_observatory_smoke.py
