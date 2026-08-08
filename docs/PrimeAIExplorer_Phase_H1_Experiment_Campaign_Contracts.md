# PrimeAIExplorer Phase H1 — Experiment & Campaign Contracts

## Purpose

Phase H1 introduces the scientific control-plane contracts used to describe
reproducible experiments and multi-experiment campaigns.

H1 defines experiments. It does not execute providers.

## Core contracts

- `DatasetSpec`
- `PromptSpec`
- `ProviderTarget`
- `TrialPolicy`
- `ReproducibilityPolicy`
- `ExecutionPolicy`
- `ExperimentDefinition`
- `CampaignSpec`
- `ExperimentManifest`
- `CampaignManifest`

## Identity rule

An experiment receives a deterministic SHA-256 identity computed from canonical
JSON over its scientific specification.

The identity is independent of execution time, workstation, output directory,
provider response, API request ID, and runtime latency.

Provider-target input order and campaign experiment input order are normalized
before identity calculation.

## Campaign planning

`CampaignSpec.total_planned_trials` is derived from:

    sum(provider targets × repetitions)

across all experiments.

## Scientific boundary

    H1 describes the experiment.
    H2-H8 will select data, execute it, analyze it, and publish it.

No provider/API calls are made in H1.

## Phase H lineage

    G8  Behavioral Observatory
     ↓
    H1  Experiment & Campaign Contracts
     ↓
    H2  Dataset & Prompt Suite Registry
     ↓
    H3  Campaign Execution Engine
     ↓
    H4  Multi-Provider Benchmark Orchestrator
     ↓
    H5  Reproducibility & Provenance Engine
     ↓
    H6  Statistical Experiment Analysis
     ↓
    H7  Benchmark Comparison & Ranking
     ↓
    H8  Experimental Observatory & Publication Bundle
