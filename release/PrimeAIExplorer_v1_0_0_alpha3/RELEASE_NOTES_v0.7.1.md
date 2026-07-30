# PrimeAIExplorer v0.7.1

## Comparative discovery and graceful handling

- Adds `compare --experiment-root` recursive analysis discovery.
- Skips comparison output folders and incomplete analyses.
- Allows explicit `--analysis` folders and discovered folders together.
- Reports discovered models and pilots before comparison.
- When fewer than two completed analyses exist, exits cleanly with guidance instead of a missing-file traceback.
- Preserves `compare-verify` and all v0.7.0 comparative artifacts.
