# PrimeAIExplorer v2.0 Phase B2.1 — Sequence Plugin API

## Purpose

B2.1 establishes the first scientific contract above the B1.x infrastructure.
The kernel remains independent of prime numbers, gaps, or any specific
mathematical family.

## Architecture

```text
SequenceDescriptor / SequenceWindowRequest
                 ↓
          SequenceProvider
                 ↓
       SequenceProviderRegistry
                 ↓
       SequenceExecutionPlugin
                 ↓
   B1.4 PluginExecutionPipeline
                 ↓
      B1.3 ExecutionEngine
                 ↓
        deterministic output
```

## Core contracts

### SequenceDescriptor

Declares sequence identity, version, value type, index origin, finiteness,
length, monotonicity, metadata, and a deterministic descriptor hash.

### SequenceWindowRequest

Selects a sequence window using an explicit mathematical index and count.

### SequenceWindow

Carries validated values, start/end indices, descriptor identity, and a stable
window hash.

### SequenceProvider

A runtime-checkable protocol with `describe()` and `read_window()`.

### SequenceExecutionPlugin

Adapts one or more providers to the generic B1.4 plugin pipeline. Supported
operations are `list`, `describe`, `window`, and `batch`.

## Index rule

`start_index` uses the mathematical index declared by `index_origin`; it is not
silently converted to a different public convention.

## Deferred work

Persistent NumPy sources, memory mapping, repository connectors, transforms,
derived sequences, streaming, remote providers, and prime-specific providers
remain separate later phases.
