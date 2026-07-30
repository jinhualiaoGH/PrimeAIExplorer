# PrimeAIExplorer v1.2.2 — Fixture Correction

This maintenance package corrects the only remaining v1.2.1 integration-test
failure.

The synthetic gap fixture contains six outgoing gaps equal to `2`, at
zero-based positions:

```text
1, 2, 4, 6, 9, 11
```

Therefore the verified v1.1.1 extractor correctly reports six left twin
values. The previous test incorrectly expected eight.

v1.2.2 also aligns the registry's Left Twin plugin version with the installed
adapter version and retains strict installer exit-code handling.

## Install

```powershell
cd C:\PrimeAIExplorer\PrimeAIExplorer_v1.2.2_Fixture_Correction

Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass

.\scripts\install_v1.2.2.ps1
```
