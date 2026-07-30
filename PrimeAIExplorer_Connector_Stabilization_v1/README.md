# PrimeAIExplorer Connector Stabilization v1

This package restores the canonical connector registry expected by the existing
PrimeAIExplorer execution engine.

It does not replace connector implementations or execution code.

## Restored records

- `CONNECTOR-000001`: deterministic mock, active, free, no external access.
- `CONNECTOR-000002`: replay, planned, free, no external access.
- `CONNECTOR-000003`: OpenAI, disabled, paid, external access.

Only the deterministic mock connector is active.

## Safety

The installer:

1. verifies `C:\PrimeAIExplorer`;
2. backs up existing connector registry files;
3. installs the canonical CSV and matching JSON;
4. validates the registry;
5. runs the focused execution-engine tests.

No external API is called.
