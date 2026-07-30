# PrimeAIExplorer Changelog

## 0.8.0 - 2026-07-25

### Added

- Canonical Execution Specification.
- Canonical run-manifest JSON Schema.
- Execution-profile registry in CSV and JSON.
- Immutable execution context.
- Canonical run identifiers.
- Canonical registry loader.
- Registry relationship validation.
- Free-mode connector governance.
- Deterministic execution cases.
- End-to-end local execution engine.
- Append-only JSON Lines event log.
- Connector-to-observation integration.
- Observation-to-evaluation integration.
- Deterministic run accounting.
- Scientific report generation.
- Atomic run-manifest writing.
- Free end-to-end demonstration.
- Execution-engine unit tests.

### Scientific policy

A run preserves both what was planned and what occurred.

Disabled, paid, or external-access connectors cannot execute in free mode.

Every connector attempt becomes a preserved observation before evaluation.

Deterministic mock output is infrastructure-validation evidence and must not be
represented as foundation-model evidence.
## 0.7.0 - 2026-07-25

### Added

- Canonical Connector Specification.
- Canonical connector-definition JSON Schema.
- Connector registry in CSV and JSON.
- Model-independent connector interface.
- Canonical connector request and response models.
- Canonical request identifiers.
- Deterministic request and response hashing.
- Connector capability declarations.
- Deterministic mock connector.
- Echo, fixed-response, deterministic-hash, and structured-prediction modes.
- Connector registration and execution service.
- Local usage and latency capture.
- Connector unit tests.

### Scientific policy

Experiments communicate with AI subjects only through canonical connectors.

The deterministic mock connector performs no external access and incurs no
financial cost.

Mock responses must never be represented as frontier-model evidence.

Provider-specific connector behavior remains separate from scientific
experiment logic.
## 0.6.0 - 2026-07-25

### Added

- Canonical Scientific Report Specification.
- Canonical scientific-report JSON Schema.
- Report-definition registry in CSV and JSON.
- Deterministic Markdown report generation.
- JSON report-manifest generation.
- Evidence-manifest hashing.
- Report-integrity hashing.
- Atomic report artifact writing.
- Experiment-level scientific report builder.
- Scientific report unit tests.

### Scientific policy

Reports communicate preserved evidence and do not replace underlying
observations, evaluations, or statistical summaries.

Results and interpretations remain explicitly separated.

Claims must remain proportional to evidence.
## 0.4.0 - 2026-07-25

### Added

- Canonical Evaluation Specification.
- Canonical evaluation-result JSON Schema.
- Evaluation registry in CSV and JSON.
- Exact-match evaluator.
- Numeric absolute-error evaluator.
- Numeric relative-error metric.
- Structured-response validity evaluator.
- Deterministic text normalization.
- Decimal-based numeric parsing.
- Atomic evaluation-result writing.
- Evaluation integrity hashing.
- Evaluation unit tests.

### Scientific policy

Raw observations and derived evaluations are separate immutable scientific
objects.

Evaluation methods and primary metrics should be defined before confirmatory
results are interpreted.
## 0.3.0 - 2026-07-25

### Added

- Canonical Observation Specification.
- Canonical observation JSON Schema.
- Empty canonical observation registries in CSV and JSON.
- Python observation reference implementation.
- Atomic observation writing.
- Deterministic observation identifiers.
- Dry-run observation construction.
- Observation integrity hashing.
- Observation unit tests.
- Observation status and evaluation-state enumerations.

### Scientific policy

Every execution attempt is treated as a permanent scientific observation.

Raw evidence is preserved independently from derived evaluation artifacts.

Dry-run records must never claim that a model call occurred.

## 0.2.0 - 2026-07-25

### Added

- Scientific Principles.
- Canonical Experiment Specification.
- Canonical Dataset Specification.
- Canonical Prompt Specification.
- Experiment, dataset, and prompt registries.

## 1.1.0 - EXP-000002 Left Twin Prime Benchmark

- Hardened the `left_twin` sequence plugin.
- Added atomic uint64 dataset generation and SHA-256 metadata.
- Added dataset validation.
- Added deterministic baseline generation.
- Added score summary generation.
- Added EXP-000002 synthetic end-to-end tests.
- Added the v1.1 pipeline commands.

## 1.1.1 - Maintenance Release

- Restored `is_probable_prime_64` as a backward-compatible alias.
- Corrected the synthetic EXP-000002 fixture.
- Added permanent compatibility regression tests.
- Made installer success contingent on all validations and tests passing.
