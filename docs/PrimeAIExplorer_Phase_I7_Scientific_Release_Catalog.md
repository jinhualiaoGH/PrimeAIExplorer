# PrimeAIExplorer Phase I7 — Scientific Release Catalog & Query Service

## Purpose

Phase I7 adds a persistent discovery layer over the trusted scientific release
pipeline established by I5 and I6.

The catalog does not replace release verification. It records release identity
and enables search only after trust status has been made explicit.

## Trust boundary

The preferred registration path is:

    I5 bundle
       ↓
    I6 verify
       ↓
    I6 inspect
       ↓
    I6 import
       ↓
    I7 record_from_verified_import(...)
       ↓
    verified catalog record

`record_from_verified_import(...)` requires consistency across:

- release ID,
- release manifest SHA-256,
- bundle SHA-256,
- imported release identity.

An invalid `ReleaseVerificationResult` is rejected.

The catalog can technically store an `UNVERIFIED` record, but query services
exclude unverified records by default. Catalog membership therefore never
silently upgrades trust.

## Catalog record

Each `ScientificReleaseCatalogRecord` contains:

- release ID,
- release name,
- campaign ID,
- experiment ID,
- release manifest SHA-256,
- bundle SHA-256,
- import path,
- explicit trust status,
- component kinds,
- evidence references,
- metadata,
- deterministic record SHA-256.

## Evidence indexing

Imported I5 `scientific_evidence.json` records are converted to
`CatalogEvidenceRef` values and indexed by:

- evidence type,
- evidence ID,
- SHA-256.

Typical evidence types include:

- `h6.result_set`
- `h6.provenance`
- `h7.analysis`
- `h8.publication`

## Persistent catalog

`ScientificReleaseCatalog` stores immutable per-release records under:

    catalog/
        records/
            <release-id>.json
        catalog.json

Registration is idempotent for an identical record and rejects a conflicting
record using the same release ID.

## Query service

`ScientificReleaseCatalogQueryService` supports deterministic queries by:

- release ID,
- release name,
- campaign ID,
- experiment ID,
- component kind,
- evidence type,
- evidence ID,
- trust status via `verified_only`.

It also exposes:

- campaign inventory,
- experiment inventory,
- evidence-type inventory.

## Deterministic export

`export_catalog_snapshot(...)` emits a canonical machine-readable catalog
snapshot containing:

- record count,
- records,
- catalog SHA-256,
- snapshot SHA-256.

## Architecture

    H1-H8 scientific workflow
             │
             ▼
    I1-I4 persistence + proof
             │
             ▼
        I5 release
             │
             ▼
      I6 verify/import
             │
             ▼
        I7 catalog
        ├─ register
        ├─ index
        ├─ query
        ├─ discover
        └─ export
             │
             ▼
    searchable scientific corpus

## Next stage

Phase I8 should integrate and freeze the complete Phase I architecture:

- I1 logical repository
- I2 durable artifacts
- I3 checkpoint/resume
- I4 reproducibility verification
- I5 deterministic release
- I6 release verification/import
- I7 catalog/query

I8 should provide end-to-end architecture contracts, integration tests,
reference workflow documentation, and the Phase I architecture freeze.
