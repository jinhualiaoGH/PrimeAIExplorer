# Phase E3 demonstration

```powershell
py -m model_invocation.cli providers
py -m model_invocation.cli health --config .\examples\phase_e3\provider_manual.json
py -m model_invocation.cli run `
    --config .\examples\phase_e3\provider_manual.json `
    --input .\examples\phase_e3\cases.jsonl `
    --output .\pipeline_runs\phase_e3\responses.jsonl
py -m metrics_engine.cli analyze `
    .\pipeline_runs\phase_e3\responses.jsonl `
    --output .\pipeline_runs\phase_e3\analysis
```
