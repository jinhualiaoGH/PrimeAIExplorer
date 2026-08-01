# PrimeAIExplorer v2.0 Phase C5

## Scientific Report and Visualization Engine

C5 consumes a Phase C4 analysis bundle and creates:

- `report.html`
- `report.md`
- `summary.json`
- `report_manifest.json`
- `figures/core_metrics.svg`
- `figures/calibration.svg`
- copied CSV tables under `tables/`

The report engine uses deterministic SVG generation and Python's standard
library only. It does not require browser automation or external plotting
packages.

Generate a report:

```powershell
py -m report_engine.cli `
    .\analysis\phase_c4_demo `
    --output .\reports\phase_c5_demo `
    --experiment-label phase-c4-demo `
    --title "PrimeAIExplorer Phase C5 Demonstration"
```

Open the HTML report:

```powershell
Start-Process .\reports\phase_c5_demo\report.html
```
