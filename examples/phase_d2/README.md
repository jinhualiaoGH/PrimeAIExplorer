# Phase D2 Example

Register an existing experiment snapshot:

```powershell
py -m experiment_catalog.cli `
    --database .\catalog_store\experiments.sqlite3 `
    register `
    .\experiments\EXP-4E3029E0A3FE6918 `
    --analysis-json .\analysis\EXP-4E3029E0A3FE6918\analysis.json `
    --report-manifest .\reports\EXP-4E3029E0A3FE6918\report_manifest.json
```

Search completed experiments:

```powershell
py -m experiment_catalog.cli `
    --database .\catalog_store\experiments.sqlite3 `
    search `
    --status completed
```

Export the catalog:

```powershell
py -m experiment_catalog.cli `
    --database .\catalog_store\experiments.sqlite3 `
    export `
    .\catalog_exports\experiments.jsonl
```
