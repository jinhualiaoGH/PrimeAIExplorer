# PrimeAIExplorer v1.0.0-alpha1 Release Notes

## Milestone A, Step A1

Introduces the observatory-core architecture beside the stable v0.7.3 engine.

### Added

- Abstract `Observatory` interface.
- Validated `ObservatoryResult` data contract.
- Ordered `ObservatoryManager` registry and runner.
- Immutable-style mappings for records, context, and results.
- Validation for duplicate/blank names, malformed records, mismatched result names, and incorrect result types.
- Eight dedicated core tests.

### Compatibility

No existing analyzer, workspace, collection, comparison, report, or CLI behavior is intentionally changed.

### Next step

A2 will migrate performance metrics into the first concrete observatory while retaining compatibility with existing reports.
