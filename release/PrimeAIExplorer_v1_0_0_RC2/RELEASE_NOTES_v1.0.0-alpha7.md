# PrimeAIExplorer v1.0.0-alpha7

Alpha7 includes the alpha6 unified export milestone and adds a self-contained HTML dashboard.

## New modules

- `primeaiexplorer.exporters.UnifiedExportEngine`
- `primeaiexplorer.dashboards.HtmlDashboardEngine`

## Unified package

The exporter writes `summary.json`, `observatories.json`, `metrics.csv`, `observatory_catalog.csv`, per-observatory table CSV files, and a SHA-256 `manifest.json`.

## Dashboard

The dashboard is one portable `dashboard.html` file with no web dependencies. It summarizes all registered observatories, metrics, tables, warnings, and analysis context.
