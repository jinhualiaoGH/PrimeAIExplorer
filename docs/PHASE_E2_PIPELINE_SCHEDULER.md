# PrimeAIExplorer v2.0 Phase E2

Phase E2 adds a deterministic dependency-aware scheduler above the Phase E1 end-to-end pipeline.

## Capabilities

- Directed acyclic graph validation
- Deterministic topological ordering
- Missing-dependency and cycle detection
- Dependency-aware stage readiness
- Atomic scheduler-state persistence
- Pause and resume through `--max-stages`
- Failure propagation and blocked-stage tracking
- Failed-stage reset
- Structured JSON planning, status, and execution summaries

## Commands

```powershell
py -m pipeline_scheduler.cli plan .\examples\phase_e2\scheduler_specification.json --state .\pipeline_runs\phase_e2\scheduler_state.json
py -m pipeline_scheduler.cli run .\examples\phase_e2\scheduler_specification.json --state .\pipeline_runs\phase_e2\scheduler_state.json
py -m pipeline_scheduler.cli status .\examples\phase_e2\scheduler_specification.json --state .\pipeline_runs\phase_e2\scheduler_state.json
```
