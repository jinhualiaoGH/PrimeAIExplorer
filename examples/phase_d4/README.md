# Phase D4 Example

Run up to five items using the deterministic demo executor:

```powershell
py -m campaign_orchestrator.cli run `
    --campaign-id CMP-XXXXXXXXXXXXXXXX `
    --campaign-database .\campaign_store\campaigns.sqlite3 `
    --orchestrator-database .\orchestrator_store\orchestrator.sqlite3 `
    --worker-id local-worker-01 `
    --executor demo `
    --max-items 5
```

Inspect events:

```powershell
py -m campaign_orchestrator.cli events `
    --campaign-id CMP-XXXXXXXXXXXXXXXX `
    --orchestrator-database .\orchestrator_store\orchestrator.sqlite3
```

Request a cooperative stop:

```powershell
py -m campaign_orchestrator.cli request-stop `
    --campaign-id CMP-XXXXXXXXXXXXXXXX `
    --orchestrator-database .\orchestrator_store\orchestrator.sqlite3 `
    --reason "operator pause"
```

The command executor receives `{input}` and `{output}` placeholders. The
external command must write an outcome JSON object such as:

```json
{
  "success": true,
  "experiment_id": "EXP-...",
  "catalog_record_id": "XR-..."
}
```
