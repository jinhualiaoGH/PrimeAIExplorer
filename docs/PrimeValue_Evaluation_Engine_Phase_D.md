# PrimeAIExplorer v1.3 Phase D

## Response contract

Each response file is named by case ID:

```text
CASE-W004-000001.json
```

and contains:

```json
{
  "prediction": 31295239,
  "confidence": 74,
  "explanation": "brief explanation",
  "latency_ms": 1250.4
}
```

`latency_ms` is optional. The other fields are required.

## Evaluation outputs

```text
experiments/EXP-000003/evaluations/<model-slug>/
├── summary.json
├── summary.md
├── case_results.json
└── case_results.csv
```

## Metrics

- exact match;
- absolute error;
- relative error;
- signed error;
- prime-valid prediction;
- response existence;
- valid JSON;
- schema validity;
- confidence summaries;
- latency summaries;
- per-window metrics.

## Leaderboard

```text
experiments/EXP-000003/leaderboard/
├── leaderboard.json
└── leaderboard.csv
```

Models are ranked by exact accuracy, then schema-valid rate, then model ID.
