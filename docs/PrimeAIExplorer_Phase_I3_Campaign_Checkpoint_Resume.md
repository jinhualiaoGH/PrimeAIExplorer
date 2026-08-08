# PrimeAIExplorer Phase I3 — Campaign Checkpoint & Resume Engine

## Purpose

Phase I3 makes long-running PrimeAIExplorer campaigns safely resumable.

I1 introduced immutable logical repository contracts.
I2 introduced durable content-addressed artifacts.
I3 introduces durable execution state.

The governing invariant is:

> Completed scientific work must survive interruption and must not be silently
> recomputed or replaced during resume.

## Core contracts

`JobCheckpoint` records job identity, completion state, attempts completed,
result SHA-256 for completed jobs, last error class for incomplete jobs, and
metadata.

`CampaignCheckpoint` binds campaign identity, experiment identity, execution
plan SHA-256, checkpoint sequence, status, the complete job checkpoint set,
parent checkpoint SHA-256, and metadata.

Every checkpoint has deterministic SHA-256 identity.

## Lineage

Sequence zero has no parent. Every later checkpoint references the SHA-256 of
its immediate predecessor. This creates explicit restart provenance.

## Completed-work preservation

Lineage auditing rejects a checkpoint chain when a completed job later becomes
incomplete or when its result SHA-256 changes.

## Resume compatibility

Resume is rejected if campaign ID, experiment ID, execution plan SHA-256, or
job set differs. A completed campaign is not resumable.

A compatible interrupted/running checkpoint returns completed and pending job
IDs, allowing the runtime layer to skip completed work.

## Persistence

Checkpoint bodies are immutable and stored under:

    checkpoints/<campaign>/<experiment>/<sequence>-<checkpoint-sha>.json

A separate replaceable latest pointer lives under:

    latest/<campaign>/<experiment>.json

Writes use temporary files, flush/fsync, and atomic replacement.

## Relationship to I1 and I2

    I1  durable logical repository
     ↓
    I2  durable content-addressed artifacts
     ↓
    I3  durable resumable execution state

## Next stage

Phase I4 should add campaign-level reproducibility verification and
reproducibility certificates across repository objects, artifacts,
checkpoints, results, provenance, analysis, and publication identities.
