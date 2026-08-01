
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
