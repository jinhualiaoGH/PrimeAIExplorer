# PrimeAIExplorer v0.2.2 Analysis Report

- Experiment: `EXP-000001`
- Pilot: `pilot_001`
- Model: `demo-model`
- Responses: **5**
- Dataset cases: **5**
- Dataset coverage: **100.00%**

## Core metrics

| Metric | Value |
|---|---:|
| Exact accuracy | 60.00% |
| Mean confidence | 68.40 |
| Brier score | 0.172120 |
| ECE | 0.380000 |
| Prediction entropy | 1.370951 bits |
| Distinct predictions | 3 |

## Results by window

| Window | Count | Accuracy | Mean confidence | Brier |
|---:|---:|---:|---:|---:|
| 4 | 1 | 100.00% | 80.00 | 0.040000 |
| 8 | 1 | 100.00% | 72.00 | 0.078400 |
| 16 | 1 | 0.00% | 61.00 | 0.372100 |
| 32 | 1 | 100.00% | 74.00 | 0.067600 |
| 64 | 1 | 0.00% | 55.00 | 0.302500 |

## Prediction distribution

| Gap | Count |
|---:|---:|
| 4 | 1 |
| 6 | 3 |
| 8 | 1 |

## Explanation observatory

Unique explanation ratio: **100.00%**  
Average explanation length: **5.00 words**

### Reasoning categories

- `frequency_prior`: 3
- `local_context`: 2
- `pattern_continuation`: 2
- `uncertainty`: 1
