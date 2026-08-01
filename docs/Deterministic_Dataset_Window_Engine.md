# Phase B2.5 — Deterministic Dataset Window Engine

B2.5 turns any registered sequence provider into reproducible observation/target
cases suitable for benchmarks, prompt generation, evaluation, and future model
training.

## Dataset specification

```json
{
  "schema_version": "1.0",
  "dataset_id": "prime-gap-next-w64",
  "dataset_version": "1.0.0",
  "sequence_id": "prime-gap",
  "title": "Next prime gap from 64 observed gaps",
  "start_index": 1,
  "case_count": 10000,
  "observation_count": 64,
  "target_count": 1,
  "stride": 1,
  "metadata": {
    "task": "next-value prediction"
  }
}
```

Case `k` starts at:

```text
start_index + k * stride
```

The provider reads exactly:

```text
observation_count + target_count
```

values. B2.5 then splits the window into immutable observation and target
components.

## Operations

```text
dataset.list
dataset.describe
dataset.case
dataset.batch
```

## Deterministic identities

Every dataset specification has a SHA-256 identity. Every generated case also
has an identity derived from:

- dataset identity;
- case index;
- source sequence;
- mathematical start index;
- observation values;
- target values;
- source descriptor identity.

This makes cases independently auditable and reproducible.

## Architecture

```text
PrimeNet / sequence provider
            ↓
SequenceDatasetSpec
            ↓
SequenceDatasetEngine
            ↓
DatasetCase
      ┌─────┴─────┐
 observation    target
```
