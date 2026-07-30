# PrimeAIExplorer v1.2.0 — Sequence Framework

PrimeAIExplorer v1.2.0 introduces a generic sequence-plugin architecture while
preserving the v1.1.1 Left Twin benchmark and its existing public API.

## Main additions

- `sequence_plugins.base.SequencePlugin`
- Declarative plugin registry in CSV and JSON
- Dynamic plugin loader
- Backward-compatible Left Twin adapter
- Reference plugins:
  - integer sequence
  - prime value
  - prime gap
  - prime square
- Generic case and prompt generation
- Plugin-specific structural validation
- Installer with backup, syntax validation, focused tests, and full regression
- Migration documentation

## Install

```powershell
cd C:\Downloads\PrimeAIExplorer_v1.2.0_Sequence_Framework

Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass

.\scripts\install_v1.2.0.ps1
```

## Validate

```powershell
cd C:\PrimeAIExplorer

py .\scripts\validate_v120.py

py -m unittest discover `
    -s .\tests `
    -v
```

## Inspect registered plugins

```powershell
py .\scripts\list_sequence_plugins.py
```

## Important compatibility guarantee

The existing module remains valid:

```python
from plugins.left_twin import is_prime_64
from plugins.left_twin import is_probable_prime_64
```

EXP-000002 remains scientifically unchanged.
