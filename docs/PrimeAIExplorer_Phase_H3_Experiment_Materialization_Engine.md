# PrimeAIExplorer Phase H3 — Experiment Materialization Engine

## Purpose

Phase H3 converts immutable H1 experiment definitions and resolved H2 scientific
inputs into deterministic concrete experiment cases.

H3 materializes execution intent. It does not call providers.

## Core components

- `SourceRecord`
- `MaterializedCase`
- `ExperimentMaterialization`
- `ExperimentMaterializer`
- `MaterializationManifest`

## Materialization contract

The H3 materializer binds:

1. the H1 experiment identity,
2. the H2 dataset descriptor identity,
3. the H2 prompt identity,
4. a source-record identity,
5. a provider/model target,
6. a repetition index,
7. a deterministic or explicit seed.

The result is an immutable `MaterializedCase`.

## Deterministic ordering

Source records are normalized by record ID.

H1 provider targets are already normalized by target ID.

Materialized cases are normalized by deterministic case ID.

Therefore input iteration order does not change the final materialization
identity.

## Seed policy

H3 implements the H1 reproducibility policies:

- `none` — no seed,
- `fixed` — use the experiment base seed,
- `derived` — derive a deterministic per-record/per-target/per-repetition seed.

An explicit `ProviderTarget.seed` overrides the experiment seed policy.

## Case identity

Each materialized case receives a deterministic ID based on canonical SHA-256
provenance:

    experiment
    + resolved input suite
    + dataset descriptor
    + source record
    + prompt
    + provider/model target
    + repetition index
    + resolved seed

The case ID does not depend on wall-clock time, workstation, output directory,
provider latency, or API request ID.

## Input contract validation

H3 requires the resolved H2 dataset to match the H1 `DatasetSpec`.

H3 also requires exactly one resolved prompt matching the H1 `PromptSpec`.

Mismatched scientific inputs are rejected before execution.

## Scientific boundary

    H1 defines experiments.
    H2 registers scientific inputs.
    H3 materializes concrete cases.
    H4 will plan campaign execution.

No provider/API calls are made in H3.
