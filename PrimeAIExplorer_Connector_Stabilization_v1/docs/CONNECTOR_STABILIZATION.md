# Connector Stabilization Decision

## Problem

`core.registry_loader.RegistryLoader.connectors()` requires:

```text
connectors/connector_registry.csv
```

The current file is empty, so connector selection fails before the execution
engine can register the deterministic mock connector.

## Canonical repair

Restore the records originally defined by the PrimeAIExplorer v0.7 connector
foundation:

```text
CONNECTOR-000001  Deterministic Mock Connector  Active
CONNECTOR-000002  Replay Connector              Planned
CONNECTOR-000003  OpenAI Connector              Disabled
```

## Free-mode contract

The active deterministic connector satisfies:

```text
cost_class      = free
external_access = false
status          = Active
```

The hosted connector remains disabled and cannot be selected in free mode.

## Architectural boundary

The CSV registry is declarative metadata.

`connectors.mock.DeterministicMockConnector` remains the executable
implementation.

`core.connector_service.ConnectorService` remains the in-memory runtime
registry.

`core.registry_loader.RegistryLoader` remains the canonical relationship
validator.
