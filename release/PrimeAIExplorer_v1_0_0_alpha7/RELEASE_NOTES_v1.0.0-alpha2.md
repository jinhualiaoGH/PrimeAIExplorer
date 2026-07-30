# PrimeAIExplorer v1.0.0-alpha2

## Milestone A — Step A2: Performance Observatory

This release adds the first concrete v1.0 observatory while preserving the complete v0.7.3 workflow and A1 core.

### Added

- `PerformanceObservatory`
- Accuracy, confidence, Brier score, ECE, prediction entropy, and error metrics
- Dataset coverage and pilot completion metrics
- Calibration-bin table
- Per-window performance table
- Canonical field aliases: `actual_gap`, `ground_truth`, or `truth`; `window` or `window_size`
- Strict record validation and explicit warnings
- Eight dedicated A2 regression tests
- Standalone Performance Observatory smoke test

### Compatibility

No existing analysis, collection, workspace, comparison, or report command is removed or changed.
