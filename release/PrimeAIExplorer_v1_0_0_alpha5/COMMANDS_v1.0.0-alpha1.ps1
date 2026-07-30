$Root = "C:\PrimeAIExplorer"
$Release = "$Root\release\PrimeAIExplorer_v1_0_0_alpha1"

cd $Release

Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass

.\install.ps1
.\run_tests.ps1
.\run_demo.ps1

# Confirm package version and new public API.
.\.venv\Scripts\python.exe -c `
    "import primeaiexplorer; from primeaiexplorer.observatories import Observatory, ObservatoryManager, ObservatoryResult; print('Version:', primeaiexplorer.__version__); print('[PASS] Observatory core imports')"

# Existing CLI remains available.
.\.venv\Scripts\paiexp.exe --help
