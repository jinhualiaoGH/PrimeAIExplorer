# PrimeAIExplorer v1.2.1 — Sequence Framework Integration Fix

This maintenance release completes the v1.2 sequence-framework integration
against the verified v1.1.1 `plugins.left_twin.LeftTwinPlugin` class API.

It fixes:

1. Helper-script project-root imports.
2. The Left Twin adapter's assumed free-function API.
3. Eager imports in `sequence_plugins.builtin`.
4. Installer error propagation.

## Install

```powershell
cd C:\PrimeAIExplorer\PrimeAIExplorer_v1.2.1_Integration_Fix

Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass

.\scripts\install_v1.2.1.ps1
```

The installer accepts the partially installed `1.2.0` state and upgrades it to
`1.2.1`. It stops immediately if any validator or test returns a nonzero exit
code.
