# PrimeAIExplorer v2.0 Phase E1

E1 adds a deterministic, resumable end-to-end pipeline boundary. A pipeline specification contains ordered command stages, required inputs, expected outputs, environment-variable names, and error policy. The engine performs preflight diagnostics, executes stages without a shell, captures stdout/stderr, atomically checkpoints state, validates output hashes on resume, and writes `pipeline_manifest.json` plus `pipeline_summary.json`.

Placeholders: `{project_root}`, `{output_root}`, `{pipeline_id}`.
