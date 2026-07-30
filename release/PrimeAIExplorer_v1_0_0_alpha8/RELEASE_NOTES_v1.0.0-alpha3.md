# PrimeAIExplorer v1.0.0-alpha3

## Milestone A3 — Behavior Observatory

This release introduces the second concrete v1.0 observatory while preserving the stable v0.7.3 analysis and comparison workflow.

### Added

- `BehaviorObservatory`
- Deterministic prediction-popularity ranking
- Persistence runs with case boundaries
- Switch, repeat, and run-length metrics
- Directed transition counts and conditional probabilities
- Per-window behavior summaries
- Standardized behavior fingerprint
- Confidence realism gap when confidence and correctness are available
- Alpha3 smoke test and focused regression tests

### Launcher correction

`run_demo.ps1` now initializes the virtual-environment Python executable explicitly, validates both executables, runs each smoke test exactly once, and restores the original working directory.

### Compatibility

The original v0.7.3 analyzer, reports, collection workspace, artifact verification, and comparative observatory remain unchanged.
