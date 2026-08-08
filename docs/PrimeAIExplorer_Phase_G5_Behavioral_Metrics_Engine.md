# PrimeAIExplorer Phase G5 — Behavioral Metrics Engine

## Purpose

Phase G5 converts immutable G1–G4 behavioral observation records into
deterministic, provider-independent scientific metrics.

G5 is completely offline. It performs no provider/API calls.

## Architecture

```text
ObservationLedger / BehavioralEvaluationRecord[]
                    |
                    v
             Phase G5 Metrics
                    |
       +------------+-------------+
       |            |             |
       v            v             v
   Accuracy      Stability     Reliability
       |            |             |
       +------------+-------------+
                    |
                    v
      Entropy / Calibration / Latency
                    |
                    v
           Token Efficiency
                    |
                    v
        Cross-Model Agreement
                    |
                    v
       BehavioralMetricsReport
```

## Metrics

### Correctness
- pass rate
- mean score

### Provider reliability
- provider error count
- provider error rate

### Stability
- surface consistency
- semantic consistency
- distinct surface answers
- distinct semantic answers

### Entropy
- surface entropy
- semantic entropy
- normalized entropy

### Calibration
- absolute confidence calibration error

### Latency
- mean
- median
- P95
- P95 / median tail ratio

### Token efficiency
- total tokens
- mean tokens
- pass-rate percentage points per 1,000 mean tokens

### Cross-model agreement
- surface agreement
- semantic agreement
- matched-trial count

## Methodological rule

Provider-level entropy is never computed by pooling answers from unrelated
tasks.

Entropy is computed within a provider/model/contract/case group first. The
provider-level metric is then a weighted mean of case-level entropy values.

This preserves the v5.5.1 methodological correction in the canonical Phase G
architecture.

## Failure semantics

Provider failures are excluded from pass-rate, entropy, consistency, and
cross-model semantic evaluation calculations.

They remain visible through provider-error counts and provider-error rates.

Thus:

```text
provider failure != model failure
```

## Phase boundary

G5 computes metrics only.

Fingerprint vectors, normalization across heterogeneous metric dimensions,
model-distance calculations, visualization, and observatory dashboards belong
to later phases.
