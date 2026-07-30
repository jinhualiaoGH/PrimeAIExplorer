# Versioning Policy

PrimeAIExplorer uses semantic versioning:

```text
MAJOR.MINOR.PATCH
```

## Major

Increment when a stable public contract becomes incompatible.

## Minor

Increment when backward-compatible capabilities are added.

## Patch

Increment for backward-compatible fixes.

## Plugin versioning

Each sequence, connector, evaluator, and report plugin has its own version.

## Experiment versioning

An experiment configuration includes a version. Material changes to:

- target selection,
- sampling,
- prompts,
- model settings,
- metrics,
- source dataset,

require a new experiment version or a new experiment ID.

## Pre-1.0 rule

Existing alpha and v0.x code remains developmental. The architecture
specification guides migration but does not retroactively declare all current
modules stable.
