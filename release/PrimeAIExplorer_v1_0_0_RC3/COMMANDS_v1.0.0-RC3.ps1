$ErrorActionPreference = "Stop"
.\install.ps1
.\.venv\Scripts\paiexp.exe --version
.\run_tests.ps1
.\.venv\Scripts\paiexp.exe doctor
.\.venv\Scripts\paiexp.exe release-check --root .
.\run_demo.ps1
.\.venv\Scripts\paiexp.exe publish --analysis .\demo_alpha8 --output .\publication_rc3
Start-Process .\publication_rc3\dashboard.html
