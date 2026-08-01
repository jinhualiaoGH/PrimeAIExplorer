# PrimeAIExplorer v2.0 Phase C1

## Deterministic Experiment Manager

Phase C1 adds deterministic experiment identity, immutable specifications,
atomic lifecycle state, append-only result records, and resumable checkpoints.

## Runtime structure

```text
experiments/
  EXP-XXXXXXXXXXXXXXXX/
    experiment.json
    state.json
    checkpoints/checkpoint.json
    results/responses.jsonl
    logs/
```

## CLI

```powershell
py -m experiment_manager.cli --root .\experiments create .\examples\phase_c1\experiment_specification.json
```
