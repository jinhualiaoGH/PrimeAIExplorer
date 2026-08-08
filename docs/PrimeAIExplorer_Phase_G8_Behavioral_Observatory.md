# PrimeAIExplorer Phase G8 — Behavioral Observatory

## Purpose

Phase G8 is the presentation and reproducible export layer for the frozen
G1-G7 behavioral science contracts.

G8 does not redefine evaluation, metrics, fingerprints, or drift semantics.

## Inputs

G8 consumes only downstream scientific artifacts:

- G5 `BehavioralMetricsReport`
- G6 `BehavioralFingerprint`
- G7 `FingerprintComparisonMatrix`
- G7 `BehavioralDriftCampaignReport`

## BehavioralObservatorySnapshot

A snapshot binds together:

- snapshot ID
- metrics report
- deterministically ordered fingerprints
- comparison matrix
- drift reports
- metadata
- deterministic SHA-256 identity

## Reproducible observatory bundle

`export_observatory_bundle()` writes:

```text
snapshot.json
provider_metrics.csv
case_metrics.csv
comparison_matrix.csv
fingerprint_features.csv
drift_features.csv
index.html
```

The HTML report is static and offline. It contains:

- provider/model summary
- fingerprint comparison matrix
- behavioral drift summary
- snapshot SHA-256 identity

## Scientific boundary

```text
G8 visualizes and reports
but does not redefine
G1-G7 scientific semantics.
```

No provider/API calls occur in G8.

No scoring, normalization, fingerprint construction, distance calculation, or
drift classification policy is reimplemented in the observatory layer.

## Future observatory extensions

Later releases may add:

- interactive charts
- fingerprint radar views
- drift timelines
- similarity heat maps
- filtering and benchmark drill-down
- downloadable research reports
- longitudinal campaign catalogs

without changing the frozen G1-G7 data contracts.
