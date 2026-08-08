# PrimeAIExplorer Phase H6 — Campaign Result Assembly & Scientific Provenance

## Purpose

Phase H6 converts H5 execution evidence into a canonical scientific result set
and an explicit provenance graph.

H6 does not execute providers and does not reinterpret model behavior. It
assembles immutable outputs from H1–H5 into a durable scientific record.

## Core components

- `CampaignResultRecord`
- `CampaignResultSet`
- `ProvenanceLink`
- `ScientificProvenance`
- `CampaignAssembly`
- `CampaignResultAssembler`
- `CampaignResultManifest`

## Identity chain

H6 verifies and preserves the full upstream chain:

    ExperimentDefinition
        ↓
    ExperimentMaterialization
        ↓
    CampaignExecutionPlan
        ↓
    CampaignExecutionRun
        ↓
    CampaignResultSet
        ↓
    ScientificProvenance

Before assembly, H6 verifies:

- experiment identity matches materialization identity,
- materialization identity matches the plan,
- plan identity matches the H5 run,
- the run contains exactly the planned job set,
- each execution record retains its planned job/case identity.

## Result records

Each H5 `JobExecutionRecord` becomes a canonical `CampaignResultRecord`.

The result retains:

- job and case identity,
- terminal execution status,
- attempt count,
- provider/model/target identity,
- terminal response or terminal error,
- provider request ID,
- lane and batch coordinates,
- execution-record SHA-256 provenance.

## Provenance links

H6 records explicit immutable links:

    materialization --materialized_from--> experiment
    plan            --planned_from-------> materialization
    run             --executed_from------> plan
    result set      --assembled_from-----> run
    result record   --result_of----------> execution job

Each provenance link has its own SHA-256 identity.

## Result manifest

`CampaignResultManifest` is a compact integrity summary suitable for later
persistence, replay, release, or external scientific verification.

It records the immutable identities of the complete H1–H6 chain and every H6
result record.

## Phase G bridge

H6 intentionally stops before semantic evaluation.

A later integration layer can consume `CampaignResultRecord.response_text` and
its provider/model/case provenance and route it into the frozen Phase G
behavioral evaluation contracts.

This preserves the architecture:

    Phase H = experimental orchestration and evidence
    Phase G = behavioral measurement and observation

## Next stage

Phase H7 should provide durable campaign evidence bundles:

- deterministic directory layout,
- JSON/JSONL exports,
- SHA-256 inventory,
- bundle manifest,
- integrity verification,
- offline replay inputs.
