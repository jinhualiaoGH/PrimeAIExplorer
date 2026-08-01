# PrimeAIExplorer v2.0 Phase B1.2 — Runtime Context Engine

## Scope

Phase B1.2 turns the B1.1 kernel primitives into a reusable runtime environment.

The runtime remains independent of prime values, prime gaps, left twins,
connectors, and model-specific behavior.

## Components

### RuntimeConfiguration

Provides immutable, hashable configuration loaded from a mapping or JSON file.

### ServiceRegistry

Provides explicit dependency registration and lookup. Duplicate registration is
rejected unless replacement is requested.

### EventBus

Publishes typed kernel events to subscribed handlers and retains event history.

### RuntimeSession

Owns:

```text
ExecutionContext
RuntimeConfiguration
ServiceRegistry
EventBus
RuntimeState
ExecutionResult
```

### Lifecycle

```text
CREATED
  -> INITIALIZED
  -> RUNNING
  -> FINISHED
  -> CLOSED
```

Failure may occur from `CREATED`, `INITIALIZED`, or `RUNNING`, followed by
`CLOSED`.

## Deferred work

Phase B1.3 will add the mathematics-independent `BenchmarkRunner` and benchmark
execution protocol. Scientific records and provenance remain deferred to B1.4.
