# PrimeAIExplorer Phase I2 — Durable Artifact Store & Content Addressing

## Purpose

Phase I2 extends the logical campaign repository introduced in I1 with a
durable binary artifact layer.

I1 stores canonical JSON scientific objects and immutable repository entries.
I2 adds arbitrary files and binary artifacts without changing I1 identities.

## Core rule

Artifact identity is content identity.

The SHA-256 digest of the artifact bytes determines the physical storage
location. Filenames, timestamps, campaign IDs, experiment IDs, and logical
artifact names do not participate in content identity.

## Content-addressed layout

Artifacts are stored as:

    blobs/<sha[0:2]>/<sha[2:4]>/<sha256>

For example:

    blobs/ab/cd/abcdef...

The two-level prefix fanout prevents very large repositories from placing every
blob in one directory.

## Supported ingestion paths

`DurableArtifactStore` supports:

- `put_bytes(...)`
- `put_stream(...)`
- `put_file(...)`

All ingestion paths produce the existing I1 `ArtifactDescriptor`.

## Streaming and large files

File ingestion hashes and copies files in configurable chunks. The default
chunk size is 1 MiB.

The implementation does not require loading a source file into memory.

## Atomicity

New blobs are copied to a temporary file in the destination directory, flushed,
fsynced, verified, and atomically installed with `os.replace`.

Existing blobs are never overwritten.

## Deduplication

If the canonical SHA-256 destination already exists and verifies correctly,
I2 reuses that physical blob.

Therefore:

    same bytes
       ↓
    same SHA-256
       ↓
    same blob path

Different logical artifact names may safely refer to the same blob.

## Integrity verification

`verify(...)` checks:

- canonical blob location,
- file existence,
- byte size,
- SHA-256.

`verify_many(...)` verifies a collection.

`ArtifactIntegrityAudit` summarizes manifest-wide integrity.

## Artifact manifest

`ArtifactStoreManifest` provides deterministic identity for a logical
collection of artifacts and reports:

- artifact count,
- unique blob count,
- logical byte size,
- deduplicated physical byte size,
- manifest SHA-256.

## Relationship to I1

I1:

    scientific JSON object
        ↓
    repository entry
        ↓
    repository manifest

I2:

    arbitrary artifact bytes
        ↓
    SHA-256 content identity
        ↓
    durable blob
        ↓
    I1 ArtifactDescriptor
        ↓
    repository entry / manifest

I2 is therefore a physical persistence service underneath the I1 logical
repository contract.

## Backend neutrality

I2 intentionally exposes an artifact-store abstraction rather than coupling
higher layers to a specific directory layout.

The first backend is the local filesystem. Later backends may preserve the same
contract over network storage or object stores.

## Next stage

Phase I3 should introduce campaign checkpoint and resume infrastructure,
including durable checkpoints, restart safety, idempotent job recovery, and
checkpoint lineage.
