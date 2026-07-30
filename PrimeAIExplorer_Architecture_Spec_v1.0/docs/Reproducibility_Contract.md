# Reproducibility Contract

Every run must preserve enough evidence to reconstruct what happened.

## Required run artifacts

```text
run.json
environment.json
configuration.json
manifest.json
cases.csv
prompt_hashes.csv
response_index.csv
metrics.csv
statistics.json
summary.md
```

## Required provenance

- PrimeAIExplorer version,
- Python version,
- operating system,
- dependency versions,
- experiment configuration hash,
- sequence plugin version,
- connector version,
- evaluator versions,
- repository identity or manifest hash,
- dataset SHA-256,
- prompt SHA-256,
- raw response SHA-256.

## Run directory

```text
runs/
└── RUN-000001/
    ├── evidence/
    ├── prompts/
    ├── responses/
    ├── metrics/
    └── reports/
```

## Immutability

Completed run evidence is append-protected. Corrections create a new run or a
versioned amendment; they do not rewrite historical evidence.
