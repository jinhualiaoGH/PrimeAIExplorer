# PrimeAIExplorer v1.0.0-alpha5 commands

cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v1_0_0_alpha5
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\install.ps1
.\run_tests.ps1
.\run_demo.ps1

.\.venv\Scripts\python.exe -c "import primeaiexplorer; from primeaiexplorer.observatories import SurpriseObservatory; print('Version:', primeaiexplorer.__version__); print('[PASS] SurpriseObservatory import')"
.\.venv\Scripts\python.exe .\test_surprise_observatory_smoke.py
