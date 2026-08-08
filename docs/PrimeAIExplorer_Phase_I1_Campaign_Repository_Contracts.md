# PrimeAIExplorer Phase I1 — Campaign Repository & Persistence Contracts

I1 begins the production-infrastructure line. It introduces immutable, content-addressed persistence for scientific objects produced by Phase H.

Repository layout:

```text
repository/
  objects/<kind>/<sha-prefix>/<sha256>.json
  entries/<campaign>/<experiment>/<kind>/<object-id>.entry.json
  manifests/<repository-id>-<manifest-sha256>.json
```

Contracts: canonical JSON; SHA-256 content addressing; immutable paths; atomic writes; deterministic manifests; object verification; campaign/experiment scoped entries; safe path components.

I2 should add binary artifact storage, streaming, deduplication, artifact linking, integrity audit, and garbage-collection safety.
