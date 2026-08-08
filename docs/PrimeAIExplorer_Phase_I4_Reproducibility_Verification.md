# PrimeAIExplorer Phase I4 — Reproducibility Verification Engine

## Purpose

Phase I4 converts the persistence guarantees of I1-I3 and the scientific
identity chain of Phase H into one campaign-level reproducibility verdict.

The central question is:

> Can PrimeAIExplorer prove that the stored campaign evidence is internally
> consistent, intact, and traceable to the scientific identities declared for
> the campaign?

I4 answers that question with a deterministic reproducibility certificate.

## Verification domains

### I1 repository verification

I4 delegates to the frozen I1 repository verifier and checks:

- repository manifest existence,
- repository entry integrity,
- canonical object SHA-256 identities.

### I2 artifact verification

I4 delegates to the frozen I2 artifact audit and checks:

- canonical blob location,
- existence,
- size,
- SHA-256,
- manifest integrity.

### I3 checkpoint verification

I4 delegates to the frozen I3 lineage audit and checks:

- checkpoint sequence continuity,
- parent SHA-256 linkage,
- campaign/experiment/plan identity,
- job-set stability,
- completed-result immutability.

### Scientific identity recording

H6/H7/H8 scientific identities are represented as typed `EvidenceIdentity`
values.

Typical examples:

- `h6.result_set`
- `h6.provenance`
- `h7.analysis`
- `h8.integration`
- `h8.publication`

I4 does not redefine those frozen scientific contracts. It records and binds
their SHA-256 identities into the reproducibility certificate.

## Reproducibility certificate

A `ReproducibilityCertificate` contains deterministic verification checks.

Each check is:

- passed,
- failed, or
- skipped.

A certificate is reproducible when no verification check failed.

Skipped checks are explicit rather than silently treated as passed.

The certificate itself has deterministic SHA-256 identity.

## Certificate manifest

`ReproducibilityCertificateManifest` provides a compact persistence/export
record containing:

- certificate ID,
- certificate SHA-256,
- campaign ID,
- experiment ID,
- reproducibility verdict,
- passed/failed/skipped counts,
- source,
- metadata,
- manifest SHA-256.

## Architectural chain

    Phase H scientific identities
              │
              ▼
    I1 logical repository
              │
              ▼
    I2 durable artifacts
              │
              ▼
    I3 checkpoint lineage
              │
              ▼
    I4 reproducibility verification
              │
              ▼
    Reproducibility Certificate

## Next stage

Phase I5 should build deterministic scientific release bundles containing:

- campaign manifest,
- artifact manifest,
- checkpoint lineage summary,
- reproducibility certificate,
- scientific identity manifest,
- release metadata,
- checksums,
- machine-readable release index.
