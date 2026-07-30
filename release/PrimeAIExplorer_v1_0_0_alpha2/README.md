# PrimeAIExplorer v1.0.0-alpha1 — Observatory Core Foundation

This internal alpha begins PrimeAIExplorer v1.0 Milestone A without changing the validated v0.7.3 analysis, comparison, workspace, or reporting behavior.

## Step A1 scope

New package:

```text
src/primeaiexplorer/observatories/
    __init__.py
    base.py
    result.py
    manager.py
```

The foundation provides:

- `Observatory`: shared abstract analysis interface.
- `ObservatoryResult`: validated, immutable-style result contract.
- `ObservatoryManager`: deterministic registration and execution.
- Duplicate-name, empty-name, invalid-result, and record/context validation.
- JSON-serializable result conversion.
- Focused regression tests alongside the complete existing test suite.

No current observatory metrics have been migrated yet. That begins in Step A2 with the Performance Observatory.

## Install

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v1_0_0_alpha1
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

## Test

```powershell
.\run_tests.ps1
.\run_demo.ps1
```

## Import example

```python
from primeaiexplorer.observatories import (
    Observatory,
    ObservatoryManager,
    ObservatoryResult,
)
```

The existing `paiexp` CLI remains compatible with the v0.7.3 command set.

## v1.0.0-alpha2 — Performance Observatory

```python
from primeaiexplorer.observatories import ObservatoryManager, PerformanceObservatory

manager = ObservatoryManager([PerformanceObservatory(calibration_bins=10)])
results = manager.run(
    records=[
        {"prediction": 6, "confidence": 80, "actual_gap": 6, "window": 4},
        {"prediction": 6, "confidence": 60, "actual_gap": 2, "window": 4},
    ],
    context={"dataset_case_count": 10, "ledger_entry_count": 5},
)
print(results["performance"].to_dict())
```

Run the dedicated smoke test from PowerShell:

```powershell
.\.venv\Scripts\python.exe .\test_performance_observatory_smoke.py
```
