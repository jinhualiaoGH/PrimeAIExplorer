# PrimeAIExplorer v2.0 Phase D1

## Dataset Management and Scientific Provenance

D1 introduces deterministic, immutable dataset registration.

Capabilities:

- canonical JSON manifests
- deterministic dataset identifiers
- SHA-256 artifact verification
- artifact size verification
- immutable registration
- idempotent re-registration
- version and sequence metadata
- train/validation/test split metadata
- provenance parameters
- parent dataset identifiers
- BOM-compatible JSON loading
- registry listing and verification

A registered dataset has this structure:

```text
dataset_store/
  DS-XXXXXXXXXXXXXXXX/
    manifest.json
    train.jsonl
    test.jsonl
```

The dataset ID is derived from the canonical manifest content, excluding the
`dataset_id` field itself. Any change in artifacts, provenance, metadata,
version, or split definition produces a different dataset ID.
