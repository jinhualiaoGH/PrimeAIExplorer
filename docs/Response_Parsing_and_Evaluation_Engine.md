# Phase B2.7 — Response Parsing and Evaluation Engine

B2.7 closes the controlled prediction loop:

```text
Dataset case
    ↓
Deterministic prompt
    ↓
Model response
    ↓
Strict JSON parser
    ↓
Ground-truth evaluation
    ↓
Deterministic evaluation record
```

## Operations

```text
response.parse
response.evaluate
response.evaluate_batch
```

## Required response schema

```json
{
  "prediction": 4,
  "confidence": 82,
  "explanation": "Brief rationale"
}
```

The parser rejects:

- invalid JSON;
- missing fields;
- unexpected fields;
- nonnumeric predictions;
- confidence outside 0–100;
- empty explanations.

## Metrics

Each evaluation record contains:

```text
exact_match
absolute_error
squared_error
confidence_error
```

For a correct prediction:

```text
confidence_error = |confidence - 100|
```

For an incorrect prediction:

```text
confidence_error = |confidence - 0|
```

Batch summaries include exact-match rate, MAE, RMSE, mean confidence, and mean
confidence error.
