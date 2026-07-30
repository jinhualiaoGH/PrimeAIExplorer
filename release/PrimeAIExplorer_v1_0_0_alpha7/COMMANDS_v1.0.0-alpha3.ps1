cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v1_0_0_alpha3
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
.\run_tests.ps1
.\run_demo.ps1

.\.venv\Scripts\python.exe -c "import primeaiexplorer; from primeaiexplorer.observatories import BehaviorObservatory; print('Version:', primeaiexplorer.__version__); print('[PASS] BehaviorObservatory import')"
.\.venv\Scripts\python.exe .\test_behavior_observatory_smoke.py
