
## 2.0.0-phase-b1.1 - Kernel Foundation

- Added immutable ExecutionContext.
- Added structured ExecutionResult.
- Added canonical events and lifecycle validation.
- Added kernel exception hierarchy.
- Added deterministic serialization and hashes.

## 2.0.0-phase-b1.2 - Runtime Context Engine

- Added immutable runtime configuration.
- Added explicit service registry.
- Added typed event bus and retained event history.
- Added validated runtime lifecycle state machine.
- Added RuntimeSession and deterministic runtime snapshots.
- Added Phase B1.2 validator, tests, and documentation.

## 2.0.0-phase-b1.2-r2 - Runtime Context Engine compatibility revision

- Rebuilt against the verified Phase B1.1 serialization API.
- Replaced the unsupported canonical_payload import with normalize.
- Added Phase B1.1 kernel API preflight validation.
- Added recovery support for the failed original B1.2 installation state.

## 2.0.0-phase-b1.3 - Deterministic Execution Engine

- Added immutable execution requests and records.
- Added executable plugin protocol and explicit dispatcher.
- Added deterministic FIFO scheduler.
- Added execution metrics and engine snapshots.
- Added synchronous success and failure execution paths.
- Added Phase B1.3 validator, tests, and documentation.

## 2.0.0-phase-b1.4 - Plugin Execution Pipeline

- Added immutable plugin manifests and registry loading.
- Added capability resolution with ambiguity protection.
- Added explicit dynamic plugin loading and protocol checks.
- Added plugin lifecycle, health checking, and cleanup.
- Connected plugin manifests to the deterministic execution engine.
- Added Phase B1.4 validator, focused tests, and documentation.

## 2.0.0-phase-b2.1 - Sequence Plugin API

- Added deterministic sequence descriptors and window contracts.
- Added integer and finite-real value validation.
- Added SequenceProvider protocol and provider registry.
- Added in-memory reference sequence provider.
- Added sequence execution adapter for list, describe, window, and batch operations.
- Integrated sequence providers with the B1.4 plugin execution pipeline.
- Added Phase B2.1 validator, focused tests, and documentation.

## 2.0.0-phase-b2.2 - Memory-Mapped Sequence Provider

- Added read-only NumPy `.npy` memory-mapped sequence provider.
- Added deterministic file identity and streaming SHA-256 calculation.
- Added integer and finite-real dtype handling.
- Added lazy mapping, boundary-safe windows, and explicit lifecycle cleanup.
- Added relative and absolute source-path support.
- Added optional expected source SHA-256 enforcement.
- Integrated mapped providers with the B2.1 sequence execution adapter.
- Added B2.2 validator, focused tests, documentation, and regression coverage.

## 2.0.0-phase-b2.2-r3 - Windows Memmap Lifecycle Correction

- Added context-manager support to NpyMemmapSequenceProvider.
- Made close() explicitly detach state and close the underlying mmap.
- Corrected focused tests so providers close before TemporaryDirectory cleanup.
- Corrected pipeline test shutdown with close_plugin().
- Added installer support for clean B2.1 and interrupted B2.2 destinations.
- Added VERSION and CHANGELOG to automatic pre-install backups.

## 2.0.0-phase-b2.3 - Partitioned Gap Sequence Provider

- Added neutral JSON gap repository manifest contract.
- Added read-only partitioned uint16 gap provider.
- Added cross-partition deterministic windows.
- Added bounded LRU memory-map cache.
- Added optional partition SHA-256 verification.
- Added plugin-pipeline integration, validation, tests, and documentation.

## 2.0.0-phase-b2.4 - PrimeNet Repository Adapter

- Added direct PrimeNet CSV gap-manifest translation.
- Added automatic and configurable column mapping.
- Added inferred partition ordinals and start indices.
- Added deterministic adapter identity.
- Reused the B2.3 zero-copy partitioned uint16 provider.
- Added validation, focused tests, regression coverage, and documentation.

## 2.0.0-phase-b2.5 - Deterministic Dataset Window Engine

- Added immutable sequence dataset specifications.
- Added deterministic observation/target case generation.
- Added dataset and case SHA-256 identities.
- Added dataset boundary validation against sequence descriptors.
- Added dataset list, describe, case, and batch operations.
- Added plugin-pipeline integration, validation, tests, and documentation.

## 2.0.0-phase-b2.6 - Deterministic Prompt Generation Engine

- Added immutable, versioned prompt-template specifications.
- Added deterministic prompt rendering from B2.5 dataset cases.
- Added strict JSON response contracts.
- Added prompt, template, and batch SHA-256 identities.
- Added normal ground-truth isolation and explicit audit exposure.
- Added prompt list, describe, generate, and batch operations.
- Added plugin-pipeline integration, validator, tests, and documentation.

## 2.0.0-phase-b2.7 - Response Parsing and Evaluation Engine

- Added strict JSON response parsing.
- Added prediction, confidence, and explanation contract validation.
- Added deterministic evaluation identities.
- Added exact-match, absolute-error, squared-error, and confidence-error metrics.
- Added batch evaluation summaries with exact-match rate, MAE, and RMSE.
- Added sequence-plugin operations for parsing and evaluation.
- Added validator, focused tests, documentation, and upgrade guidance.
