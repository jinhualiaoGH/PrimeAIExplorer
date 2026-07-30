# Evaluation Contract

## Common metrics

- parse success,
- JSON compliance,
- exact match,
- absolute error,
- relative error,
- predicted gap,
- target gap,
- absolute gap error,
- confidence,
- latency,
- structural validity.

## Sequence-specific metrics

Sequence plugins may contribute additional evaluators, including:

- rank error,
- valid prime,
- valid left twin prime,
- valid constellation,
- event-language validity.

## Canonical metric record

```json
{
  "run_id": "RUN-000001",
  "case_id": "CASE-000001",
  "connector_id": "mock",
  "metric_id": "absolute_error",
  "value": 12,
  "status": "valid",
  "evaluator_version": "1.0.0"
}
```

## Rules

- Metrics must not mutate responses.
- Parsing failure must be recorded, not silently coerced.
- Boolean values must not be accepted as integers.
- Non-finite numeric values must be rejected.
- Every metric implementation must be versioned.
- Aggregate statistics must be reproducible from case-level metric records.
