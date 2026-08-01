# PrimeAIExplorer v2.0 Phase D4

## Automatic Campaign Orchestration Engine

D4 turns a D3 campaign from a persistent work plan into an automatically
processed execution stream.

Capabilities:

- automatic lowest-ordinal work-item claiming
- worker IDs
- orchestration leases
- worker heartbeat support
- stale-lease recovery
- bounded retries
- retry backoff
- maximum-item limits for controlled runs
- cooperative stop requests
- structured SQLite event logs
- experiment-ID attachment
- D2 catalog-record attachment
- pluggable executors
- deterministic offline demo executor
- external command executor for C1-C5 integration

The command executor isolates orchestration from scientific execution. It writes
the claimed D3 work item to a JSON input file and expects an outcome JSON file.
This preserves the existing C1-C5 boundaries while allowing an integration
script to:

1. create the C1 experiment specification,
2. execute it through C2 and C3,
3. analyze it through C4,
4. render the C5 report,
5. register the snapshot through D2,
6. return the resulting experiment and catalog record IDs.
