# PrimeAIExplorer v0.7.1

PrimeAIExplorer is a reproducible collection, analysis, behavior, and comparative observatory for prime-gap continuation experiments.

## Core workflows

- `workspace`: interactive response collection and automatic pilot analysis.
- `analyze`: generate one pilot/model Behavior Observatory.
- `compare`: combine two or more analysis folders into an experiment-level Comparative Observatory.
- `compare-verify`: verify all comparative artifacts and the summary hash.

Run `paiexp --help` and `paiexp compare --help` for details.


## v0.7.1 automatic comparison discovery

```powershell
paiexp compare --experiment-root C:\PrimeAIExplorer\experiments\exp000001 --output C:\PrimeAIExplorer\experiments\exp000001\comparison_v071
```

The scanner finds folders containing both `summary.json` and `manifest.json`, skips comparative-output folders, and gives a friendly status message when fewer than two completed analyses are available.
