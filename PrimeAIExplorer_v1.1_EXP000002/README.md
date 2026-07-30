# PrimeAIExplorer v1.1 — EXP-000002

This upgrade integrates the Left Twin Prime Continuation benchmark into the
stabilized PrimeAIExplorer platform.

## Capabilities

- validates canonical PrimeNet prime/gap partitions;
- extracts `ltp(1)` through `ltp(100,000,001)`;
- writes an atomic `uint64` NumPy dataset;
- writes dataset provenance and SHA-256 metadata;
- validates sequence ordering and canonical initial values;
- generates absolute, gap, and combined cases;
- generates hidden-definition and disclosed-definition prompts;
- generates deterministic baseline responses;
- scores AI and baseline responses with structural validity;
- includes a synthetic end-to-end smoke test requiring no large repository.

## Safety

The installer backs up every existing file it replaces. It does not modify
PrimeNet repository files and does not run the 100-million-value build
automatically.
