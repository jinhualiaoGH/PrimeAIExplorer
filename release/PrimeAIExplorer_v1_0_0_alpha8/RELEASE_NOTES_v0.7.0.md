# PrimeAIExplorer v0.7.0 — Comparative Observatory

PrimeAIExplorer v0.7.0 adds experiment-level comparison across two or more pilot analysis folders.

## New commands

- `paiexp compare` — combines multiple completed analysis artifact sets.
- `paiexp compare-verify` — validates the comparative artifact set and summary hash.

## New comparative artifacts

- `comparison_summary.json`
- `model_comparison.csv`
- `fingerprint_matrix.csv`
- `window_comparison.csv`
- `rankings.csv`
- `report.md`
- `report.html`
- `manifest.json`

## Scientific safeguards

Rankings are descriptive. Comparisons should use the same canonical dataset and compatible collection protocols whenever possible. The report preserves sample sizes so incomplete or unequal pilots remain visible.
