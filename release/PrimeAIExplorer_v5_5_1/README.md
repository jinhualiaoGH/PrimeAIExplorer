# PrimeAIExplorer v5.5.1 — Fingerprint Contract Repair

Corrective release for v5.5. Repairs dashboard/statistics field-name drift and adds offline re-analysis of stored v5.5 trial JSON files.

## Fixes
- Per-case dashboard now reads the actual `surface_*` and `semantic_*` fields.
- Removes browser-visible `undefined` for distinct-answer metrics.
- Provider entropy uses `mean_case_semantic_entropy_bits`.
- Surface and semantic consistency, diversity, entropy, and modal answers are displayed separately.
- `--rebuild-run RUN_ID` rebuilds analysis from stored raw trial JSON without provider/API calls.

## Fresh run
```powershell
py demo.py --provider all --trials 5
```

## Offline repair of an existing v5.5 run
```powershell
py demo.py --rebuild-run 20260807T221928Z
```
