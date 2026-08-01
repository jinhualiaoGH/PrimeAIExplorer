# Phase D3 Example

Build a deterministic campaign specification:

```powershell
py -m benchmark_campaign.cli build-spec `
    --name "Prime Gap Multi-Provider Pilot" `
    --description "Deterministic Phase D3 benchmark campaign." `
    --dataset-id DS-AAAAAAAAAAAAAAAA `
    --provider-model manual=manual-pilot `
    --provider-model openai=model-a `
    --provider-model openai=model-b `
    --prompt-template prime-gap-next-json-v1 `
    --random-seed 20260801 `
    --window-size 4 `
    --window-size 8 `
    --window-size 16 `
    --repeats 1 `
    --output .\campaign_store\pilot_specification.json
```

Expand the campaign:

```powershell
py -m benchmark_campaign.cli expand `
    .\campaign_store\pilot_specification.json `
    --output .\campaign_store\pilot_plan.json
```

Create the persistent campaign:

```powershell
py -m benchmark_campaign.cli create `
    .\campaign_store\pilot_plan.json `
    --database .\campaign_store\campaigns.sqlite3
```
