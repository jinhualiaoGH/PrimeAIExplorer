# PrimeAIExplorer Phase G6 — Behavioral Fingerprint Engine

## Purpose

Phase G6 converts provider-level G5 behavioral metrics into deterministic,
schema-bound behavioral fingerprints.

G6 remains offline and provider-independent.

## Scientific contract

```text
same G5 metrics
+ same fingerprint schema
+ same provenance
        |
        v
same ordered feature vector
        |
        v
same canonical serialization
        |
        v
same SHA-256 fingerprint identity
```

## Components

### FingerprintSchema
Defines:
- feature order
- directionality
- normalization bounds
- deterministic schema SHA-256 identity

### FingerprintNormalizer
Maps raw metric values into normalized feature coordinates.

Directionality is explicit:

```text
higher_is_better
lower_is_better
neutral
```

The normalized vector is oriented so that, when directionality is meaningful,
larger values indicate more favorable behavior.

### BehavioralFingerprint
Preserves:
- provider/model identity
- observation counts
- raw G5 metrics
- per-feature metadata
- normalized vector
- provenance
- schema identity
- fingerprint SHA-256

Raw metrics are never discarded.

### Fingerprint comparison
G6 provides deterministic:
- Euclidean distance
- Manhattan distance
- cosine similarity

Missing dimensions are excluded pairwise. Fingerprints using different schemas
cannot be compared directly.

## Default G6 feature schema

The default schema uses:

- pass rate
- mean score
- provider error rate
- calibration error
- surface consistency
- semantic consistency
- surface entropy
- semantic entropy
- median latency
- P95 latency
- latency tail ratio
- mean tokens
- token efficiency

## Scope boundary

G6 defines reproducible fingerprint vectors and direct pairwise comparison.

Longitudinal drift, baseline/reference fingerprints, population-scale
normalization, distance matrices, clustering, embeddings, and visualization
belong to later phases.
