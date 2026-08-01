# Phase E5 Example

Build a reproducibility bundle from a completed Phase E3 pipeline run:

```powershell
py -m reproducibility_bundle.cli build `
    --project-root . `
    --output-root .\reproducibility_bundles `
    --bundle-name phase_e5_demo `
    --source .\pipeline_runs\phase_e3 `
    --source .\examples\phase_e3 `
    --metadata-json .\examples\phase_e5\metadata.json `
    --reproduce-command py -m model_invocation.cli run .\examples\phase_e3\invocation_specification.json
```

Verify it:

```powershell
py -m reproducibility_bundle.cli verify `
    .\reproducibility_bundles\phase_e5_demo
```
