# PrimeAIExplorer Phase I6 — Scientific Release Verification & Import Engine

## Purpose

Phase I6 is the inverse trust boundary of I5.

I5 creates deterministic scientific release bundles.
I6 receives a bundle in a fresh environment, verifies it independently, and
imports it only when the release is internally consistent.

## Verification model

`ScientificReleaseVerifier` checks:

- ZIP readability,
- safe relative paths,
- presence of required release files,
- release manifest SHA-256 identity,
- release index consistency,
- component presence,
- component SHA-256 values,
- checksum-manifest consistency,
- campaign and experiment identity consistency,
- component index consistency,
- optional expected bundle SHA-256.

Verification produces `ReleaseVerificationResult`.

A release is valid only when the error set is empty.

## Import model

`ScientificReleaseImporter` always verifies before import.

Verified releases are imported under:

    <import-root>/
        releases/
            <release-id>/
                manifests/
                release/

Import properties:

- no extraction before verification,
- safe path resolution,
- immutable imported files,
- idempotent re-import of identical releases,
- conflict rejection,
- atomic file installation,
- import marker containing the source bundle SHA-256.

## Path safety

I6 rejects:

- absolute ZIP paths,
- `..` traversal,
- paths escaping the release destination.

The importer constructs each destination from normalized POSIX ZIP path parts
and verifies containment before writing.

## Independent inspection

`inspect_release(...)` verifies the bundle first, then exposes a compact,
read-only release view:

- release ID,
- release name,
- campaign ID,
- experiment ID,
- release manifest SHA-256,
- component inventory.

## Round-trip contract

    original environment
          │
          ▼
    I5 deterministic release
          │
          ▼
       transfer
          │
          ▼
    I6 verify
          │
          ├─ bundle SHA
          ├─ manifest SHA
          ├─ component SHA
          ├─ checksums
          ├─ index linkage
          └─ path safety
          │
          ▼
    I6 import
          │
          ▼
    reconstructed release evidence

## Non-goal

I6 does not yet materialize large external I2 artifact blobs that are merely
referenced by an artifact manifest. That belongs to repository/archive transport
and catalog work.

## Next stage

Phase I7 should introduce a persistent scientific release catalog and query
service:

- catalog release identities,
- index campaigns and experiments,
- search by evidence type,
- locate reproducibility certificates,
- list imported releases,
- query lineage and publication relationships,
- support stable machine-readable catalog exports.
