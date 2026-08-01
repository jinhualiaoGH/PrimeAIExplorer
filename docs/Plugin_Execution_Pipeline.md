# PrimeAIExplorer v2.0 Phase B1.4 — Plugin Execution Pipeline

## Purpose

B1.4 links declarative plugin registration to deterministic execution without
placing mathematical sequence logic in the kernel.

## Flow

```text
Plugin manifest
  -> ManifestRegistry
  -> CapabilityResolver
  -> PluginLoader
  -> PluginLifecycle health check
  -> B1.3 PluginDispatcher
  -> B1.3 ExecutionEngine
  -> ExecutionRecord and output
```

## Design rules

- manifests are immutable and hashable;
- disabled plugins cannot load;
- capability ambiguity requires an explicit preferred plugin;
- the loaded plugin ID must equal the manifest plugin ID;
- a plugin must pass its health check before registration with the engine;
- plugin exceptions remain governed by the B1.3 execution contract;
- module loading uses explicit manifest paths, not eager package imports.

## Deferred work

Dependency graphs, process isolation, signed plugin packages, asynchronous
workers, remote plugins, and hot reload are intentionally deferred.
