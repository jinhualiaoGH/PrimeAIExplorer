# PrimeAIExplorer v1.3.0 Release Guide

Phase E installs:

```text
VERSION = 1.3.0-rc1
```

Run:

```powershell
py .\scripts\validate_v130_release.py
py .\scripts\build_v130_release.py
py .\scripts\validate_release_archive.py
```

After a clean acceptance run:

```powershell
"1.3.0" | Set-Content .\VERSION -Encoding ascii

git add .
git commit -m "Release PrimeAIExplorer v1.3.0"

git tag -a `
    v1.3.0 `
    -m "PrimeAIExplorer v1.3.0"

git push origin main
git push origin v1.3.0
```
