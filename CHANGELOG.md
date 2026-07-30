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

## 1.2.0 - Sequence Framework

- Added the generic SequencePlugin contract.
- Added declarative CSV and JSON plugin registries.
- Added dynamic plugin loading.
- Added a compatibility-preserving Left Twin adapter.
- Added Integer Sequence, Prime Value, Prime Gap, and Prime Square plugins.
- Added generic case, prompt, and prediction-evaluation support.
- Added v1.2 validation and regression tests.

## 1.2.1 - Sequence Framework Integration Fix

- Corrected project-root imports for helper scripts.
- Rebuilt the Left Twin adapter against the verified v1.1.1 class API.
- Removed eager built-in plugin imports.
- Added explicit native exit-code checks to the installer.
- Added adapter integration regression tests.

## 1.2.2 - Fixture Correction

- Corrected the synthetic Left Twin source-validation expectation from 8 to 6.
- Added an explicit assertion for the six selected synthetic Left Twin values.
- Aligned the registry and adapter Left Twin versions at 1.2.2.
- Retained strict installer exit-code handling.

## 1.3.0-phase-a - Prime Value Plugin Contract

- Added production PrimeValueSequencePlugin configuration support.
- Added read-only PrimeNet partition discovery and source validation.
- Added EXP-000003 configuration and synchronized registries.
- Added EXP-000003 dry-run validation and focused tests.
- Explicitly deferred dataset construction and validation to Phase B.

## 1.3.0-phase-c - Prime Value Case and Prompt Engine

- Added deterministic benchmark endpoint sampling.
- Added public/private case separation.
- Added blind prompt generation.
- Added stable case, answer-key, prompt, and manifest hashes.
- Added one-based scientific index metadata.
- Added overwrite protection and atomic corpus generation.
- Added complete corpus validation and leakage checks.

## 1.3.0-phase-d - Prime Value Evaluation Engine

- Added strict per-case response parsing.
- Added exact and numerical scoring.
- Added prime-validity, confidence, and latency metrics.
- Added per-window aggregation.
- Added deterministic JSON, CSV, and Markdown reports.
- Added multi-model leaderboard generation.
- Added evaluation overwrite protection and atomic outputs.

## 1.3.0-rc1 - Release Hardening

- Added end-to-end release acceptance validation.
- Added dataset, benchmark, evaluation, and Git audits.
- Added deterministic source manifest and ZIP packaging.
- Added release archive validation.
- Added CI workflow, release guide, notes, and checklist.
