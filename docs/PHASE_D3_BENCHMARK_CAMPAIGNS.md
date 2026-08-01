# PrimeAIExplorer v2.0 Phase D3

## Multi-Provider Benchmark Campaign Manager

D3 defines one scientific benchmark campaign across:

- D1 dataset IDs
- model providers
- provider-specific models
- prompt templates
- random seeds
- observation window sizes
- deterministic repeat indices
- provider and model parameters

The campaign specification produces a deterministic `CMP-...` identifier.
Expansion creates immutable `WI-...` work items in canonical order.

The SQLite campaign manager supports:

- idempotent campaign creation
- atomic next-item claiming
- resumable campaign execution
- attempt counting
- completed experiment IDs
- D2 catalog record IDs
- failure recording
- failed-item reset
- progress summaries
- status filtering
- deterministic JSONL execution-plan exports

D3 does not duplicate C1-C5 execution logic. A future runner can claim a work
item, create and execute the corresponding C1/C2 experiment through the
existing provider layer, analyze it with C4, report it with C5, register it
with D2, and finally attach the resulting IDs to the D3 work item.
