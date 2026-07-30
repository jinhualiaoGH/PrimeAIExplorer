cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v1_0_0_alpha7
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
.\run_tests.ps1
.\run_demo.ps1
Start-Process .\demo_alpha7\dashboard.html
