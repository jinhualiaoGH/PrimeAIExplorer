# PrimeAIExplorer v1.0.0-alpha4

PrimeAIExplorer is a reproducible research platform for collecting, analyzing, comparing, and publishing controlled AI prime-gap continuation experiments.

## Milestone A observatories

- **Performance Observatory** — accuracy, confidence, Brier score, ECE, entropy, coverage, completion, and window metrics.
- **Behavior Observatory** — popularity, persistence, switching, runs, transitions, and behavior fingerprints.
- **Calibration Observatory** — reliability bins, ECE, maximum calibration error, signed bias, over/underconfidence, and window calibration.
- **Distribution Observatory** — prediction, truth, and error spectra; confusion structure; entropy; error direction; total variation; Jensen-Shannon divergence; and window distributions.

## Install and validate

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v1_0_0_alpha4
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
.\run_tests.ps1
.\run_demo.ps1
```

Expected test result:

```text
Ran 75 tests

OK
```

## Direct smoke tests

```powershell
.\.venv\Scripts\python.exe .\test_performance_observatory_smoke.py
.\.venv\Scripts\python.exe .\test_behavior_observatory_smoke.py
.\.venv\Scripts\python.exe .\test_calibration_observatory_smoke.py
.\.venv\Scripts\python.exe .\test_distribution_observatory_smoke.py
```

## Combined execution

```python
from primeaiexplorer.observatories import (
    BehaviorObservatory,
    CalibrationObservatory,
    DistributionObservatory,
    ObservatoryManager,
    PerformanceObservatory,
)

manager = ObservatoryManager([
    PerformanceObservatory(),
    BehaviorObservatory(),
    CalibrationObservatory(),
    DistributionObservatory(),
])

results = manager.run(records, context)
```

Execution order is deterministic and follows registration order.

## Compatibility

The inherited PrimeAIExplorer v0.7.3 collection, analysis, verification, comparison, and report workflow remains available and is exercised by `run_demo.ps1`.

## v1.0.0-alpha5 Surprise Observatory

The v1.0 observatory manager can now run five first-class observatories in a
deterministic sequence: Performance, Behavior, Calibration, Distribution, and
Surprise. The Surprise Observatory identifies rare predictions and truths,
novel predictions, confidence mismatches, large errors, and unexpected
prediction transitions.

## v1.0.0-alpha7 unified dashboard

Run `run_demo.ps1`, then open `demo_alpha7\dashboard.html`. The accompanying portable analysis package is stored in `demo_alpha7`.

## v1.0.0-alpha8 visualization layer

Alpha8 adds `SvgVisualizationEngine`, standalone SVG figure export, a figure catalog, and embedded visualization panels in the self-contained HTML dashboard.
