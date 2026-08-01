# PrimeAIExplorer v2.0 Phase D2

## Persistent Experiment Registry and Search

D2 introduces a standard-library SQLite catalog that links:

- D1 dataset identifiers
- C1 experiment specifications
- C2 execution state
- C3 provider and model metadata
- C4 accuracy and error metrics
- C5 report manifests

Each registration creates an immutable content-addressed snapshot with:

- deterministic `XR-XXXXXXXXXXXXXXXX` record ID
- SHA-256 snapshot digest
- experiment ID and name
- dataset ID
- provider and model
- sequence type
- execution status
- case and failure counts
- accuracy and mean absolute error
- report path
- timestamps
- complete source snapshot JSON

Multiple snapshots of the same experiment are preserved, allowing lifecycle
history such as `created -> running -> completed`.

Search indexes cover experiment ID, dataset ID, provider, model, status,
sequence type, and accuracy.
