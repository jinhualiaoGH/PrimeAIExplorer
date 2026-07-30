# PrimeAIExplorer v1.0.0-alpha5

## Milestone A5 — Surprise Observatory

This release adds a first-class `SurpriseObservatory` beside the existing
Performance, Behavior, Calibration, and Distribution observatories.

### New measurements

- empirical truth rarity in bits
- empirical prediction rarity in bits
- prediction novelty and first occurrence
- confidence surprise
- error-magnitude surprise
- directed transition surprise
- per-record composite surprise index
- ranked top-surprise events
- cumulative surprise timeline
- per-window surprise summaries

### Standardized tables

- `surprise_events`
- `surprise_timeline`
- `novel_predictions`
- `window_surprise`
- `unexpected_transitions`
- `top_surprises`

The composite index is transparent and descriptive: it is the arithmetic mean
of truth rarity, prediction rarity, confidence surprise, error surprise, and,
when available, transition surprise.

### Validation

The complete suite contains 84 tests: 75 inherited tests and 9 new Surprise
Observatory tests.
