# Module Ownership

Each capability must have one authoritative owner.

| Capability | Authoritative module |
|---|---|
| Configuration loading | `core.config` |
| Plugin discovery | `core.registry` |
| PrimeNet access | `core.repository_adapter` |
| Case generation | `core.experiment_engine` |
| Prompt rendering | `core.prompt_engine` |
| Connector selection | `core.registry_loader` |
| Model execution | `core.execution_engine` |
| Response parsing | `core.response_parser` |
| Metric computation | `core.evaluation_engine` |
| Run persistence | `core.run_store` |
| Reporting | `core.report_engine` |
| Publication output | `publication` |

## Rules

- No duplicate registries for the same plugin category.
- No connector-specific behavior in the sequence engine.
- No sequence-specific behavior in the connector engine.
- No answer-key access from connectors.
- No report generation inside metric plugins.
- No direct PrimeNet file access outside the repository adapter and approved
  sequence plugins.
