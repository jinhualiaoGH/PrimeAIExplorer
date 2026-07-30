# Experiment Format

Experiments are declarative and immutable after execution begins.

## Required sections

```json
{
  "experiment": {},
  "repository": {},
  "sequence": {},
  "sampling": {},
  "prompt": {},
  "execution": {},
  "evaluation": {},
  "paths": {}
}
```

## Example

```json
{
  "experiment": {
    "id": "EXP-000002",
    "name": "Left Twin Prime Continuation",
    "version": "1.0.0"
  },
  "repository": {
    "prime_root": "E:/PrimeNet/Repository/ranges",
    "gap_root": "E:/PrimeNet/Repository/gaps_u16",
    "read_only": true
  },
  "sequence": {
    "plugin": "left_twin",
    "target_count": 100000001,
    "dataset_file": "data/left_twin_primes.u64.npy"
  },
  "sampling": {
    "endpoints": [1000, 10000, 100000000],
    "window_sizes": [4, 8, 16, 32, 64],
    "representations": ["absolute", "gaps", "combined"],
    "definition_conditions": ["hidden", "disclosed"]
  },
  "prompt": {
    "template_id": "numeric_continuation_json_v1",
    "target_label": "left twin prime"
  },
  "execution": {
    "connectors": ["mock"],
    "temperature": 0,
    "timeout_seconds": 120,
    "retry_count": 2
  },
  "evaluation": {
    "metrics": [
      "exact_match",
      "absolute_error",
      "relative_error",
      "structural_validity"
    ]
  },
  "paths": {
    "experiment_root": "experiments/EXP-000002"
  }
}
```

## Immutability

When a run begins, the normalized configuration must be copied into the run
directory and hashed. Later edits to the source configuration must not change
the historical run.
