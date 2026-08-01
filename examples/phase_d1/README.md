# Phase D1 Example

Build a deterministic dataset manifest:

```powershell
py -m dataset_registry.cli build-manifest `
    .\examples\phase_d1\data `
    --name "Prime Gap Fixture" `
    --version "1.0.0" `
    --description "Small deterministic D1 example." `
    --sequence-type "prime-gap" `
    --generated-by "PrimeAIExplorer Phase D1" `
    --generated-at-utc "2026-08-01T12:00:00Z" `
    --source-type "synthetic" `
    --source-reference "examples/phase_d1" `
    --artifact train.jsonl `
    --artifact test.jsonl `
    --output .\examples\phase_d1\manifest.json
```

Verify:

```powershell
py -m dataset_registry.cli verify `
    .\examples\phase_d1\data `
    .\examples\phase_d1\manifest.json
```

Register immutably:

```powershell
py -m dataset_registry.cli register `
    .\examples\phase_d1\data `
    .\examples\phase_d1\manifest.json `
    --registry-root .\dataset_store
```
