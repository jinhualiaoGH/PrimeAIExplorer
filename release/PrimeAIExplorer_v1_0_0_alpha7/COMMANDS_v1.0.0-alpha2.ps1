# PrimeAIExplorer v1.0.0-alpha2 — A2 validation commands
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v1_0_0_alpha2

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\install.ps1
.\run_tests.ps1
.\run_demo.ps1

.\.venv\Scripts\python.exe -c "import primeaiexplorer; from primeaiexplorer.observatories import PerformanceObservatory; print('Version:', primeaiexplorer.__version__); print('[PASS] PerformanceObservatory import')"

.\.venv\Scripts\python.exe .\test_performance_observatory_smoke.py
