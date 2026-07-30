$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
.\run_tests.ps1
.\.venv\Scripts\paiexp.exe doctor --json-output .\doctor_report.json
.\.venv\Scripts\paiexp.exe release-check --root . --json-output .\release_check.json
.\run_demo.ps1
