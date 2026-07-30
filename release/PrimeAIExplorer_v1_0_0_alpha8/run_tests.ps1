$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root ".venv\Scripts\python.exe") -m unittest discover -s (Join-Path $Root "tests") -v
