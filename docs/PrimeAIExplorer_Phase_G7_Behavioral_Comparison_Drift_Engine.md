# PrimeAIExplorer Phase G7 — Behavioral Comparison & Drift Engine

## Purpose

Phase G7 compares frozen G6 behavioral fingerprints across providers, models,
versions, and campaigns.

G7 is offline, deterministic, and provider-independent.

## Scientific distinction

Behavioral movement is not automatically quality regression:

```text
behavioral distance != degradation
```

G7 therefore records both:

1. magnitude of movement; and
2. feature-level interpretation.

Because G6 direction-orients quality-sensitive coordinates, positive movement
means improvement and negative movement means degradation for those features.
Neutral features are labeled simply as changed.

## Components

### FingerprintBaselineRegistry

Stores named reference fingerprints without modifying them.

### FeatureDrift

For each comparable coordinate:

- baseline normalized value
- current normalized value
- signed delta
- absolute delta
- directionality
- interpretation

Interpretations:

- unchanged
- improvement
- degradation
- changed
- not_comparable

### BehavioralDriftReport

Uses root-mean-square normalized feature movement as the aggregate drift score.
RMS keeps the score comparable when the number of usable dimensions changes.

Default classifications:

- stable: <= 0.05
- minor: <= 0.15
- material: <= 0.30
- major: > 0.30

Thresholds are explicit and configurable.

### FingerprintComparisonMatrix

Builds a deterministic N x N comparison matrix containing:

- comparable feature count
- Euclidean distance
- Manhattan distance
- cosine similarity

Subjects are sorted by `provider/model`, and duplicate subjects are rejected.

### BehavioralDriftCampaignReport

Compares a deterministic collection of fingerprints against a named baseline.

## Scope boundary

G7 does not perform clustering, dimensionality reduction, visualization,
dashboards, alerting, or automatic model-quality judgments.

Those belong to later observatory phases.
