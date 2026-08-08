# PrimeAIExplorer Phase I5 — Scientific Release Bundle Builder

## Purpose

Phase I5 converts a verified PrimeAIExplorer campaign into a deterministic,
portable scientific release bundle.

I1-I4 establish:

- logical repository identity,
- durable artifact identity,
- checkpoint lineage,
- reproducibility certification.

I5 packages those identities into one immutable release artifact.

## Bundle structure

A release ZIP contains a deterministic layout:

    manifests/
        repository.json
        artifacts.json
        checkpoints.json
        reproducibility_certificate.json
        scientific_evidence.json

    release/
        metadata.json
        manifest.json
        index.json
        checksums.sha256

Only components supplied to the builder are included.

## Logical and physical identity

I5 distinguishes two identities.

### Release manifest SHA-256

This is the logical identity of the scientific release.

It is derived from:

- release name,
- campaign ID,
- experiment ID,
- ordered component identities,
- release metadata.

### Bundle SHA-256

This is the physical SHA-256 of the deterministic ZIP bytes.

The bundle uses:

- sorted entry names,
- canonical JSON,
- fixed ZIP timestamps,
- fixed file permissions,
- no ZIP compression variability.

Therefore identical release inputs produce identical bundle bytes.

## Release components

I5 supports the following component kinds:

- I1 repository manifest,
- I2 artifact manifest,
- I3 checkpoint lineage,
- I4 reproducibility certificate,
- H6/H7/H8 scientific evidence identities,
- release metadata.

I5 does not copy large I2 blob payloads into the bundle yet. The artifact
manifest records their immutable content identities. Portable blob materializing
and import/verification belong to the next release transport layer.

## Checksums

`release/checksums.sha256` contains SHA-256 values for every included release
component plus the release manifest.

## Release index

`release/index.json` is a compact machine-readable entry point containing:

- release ID,
- release name,
- campaign and experiment identity,
- release manifest SHA-256,
- component count,
- component paths and hashes,
- manifest/checksum locations.

## Determinism contract

Given identical logical inputs, I5 guarantees:

    same component bytes
        ↓
    same component SHA-256
        ↓
    same release manifest
        ↓
    same release manifest SHA-256
        ↓
    same deterministic ZIP bytes
        ↓
    same bundle SHA-256

## Relationship to earlier phases

    H6/H7/H8 scientific identities
              │
              ▼
    I1 Repository Manifest
              │
              ▼
    I2 Artifact Manifest
              │
              ▼
    I3 Checkpoint Lineage
              │
              ▼
    I4 Reproducibility Certificate
              │
              ▼
    I5 Scientific Release Bundle

## Next stage

Phase I6 should implement release verification and import:

- open an I5 bundle,
- validate deterministic paths,
- verify checksums,
- reconstruct release manifest,
- verify component identities,
- optionally verify referenced I2 blobs,
- import safely into a local repository,
- reject malformed or conflicting releases.
