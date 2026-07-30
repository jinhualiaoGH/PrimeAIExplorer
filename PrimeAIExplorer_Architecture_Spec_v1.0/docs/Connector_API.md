# Connector API

## Purpose

A connector adapts one model provider or local model runtime to the common
PrimeAIExplorer request and response contracts.

## Required metadata

```python
connector_id: str
provider: str
model_id: str
connector_version: str
pricing_class: str
supports_structured_output: bool
supports_tools: bool
```

## Required methods

```python
validate() -> ValidationReport
capabilities() -> ConnectorCapabilities
execute(request: ConnectorRequest) -> ConnectorResponse
```

## Connector request

```json
{
  "request_id": "REQ-000001",
  "experiment_id": "EXP-000002",
  "case_id": "CASE-000001",
  "system_message": "...",
  "user_message": "...",
  "temperature": 0,
  "timeout_seconds": 120
}
```

## Connector response

```json
{
  "request_id": "REQ-000001",
  "status": "success",
  "raw_text": "...",
  "latency_seconds": 1.23,
  "usage": {},
  "provider_metadata": {}
}
```

## Security requirements

- API keys must come from environment variables or approved secret stores.
- API keys must never be written to logs, manifests, prompts, or reports.
- Registry files may name an environment variable but must not contain its value.
- Mock connectors must perform no external access.

## Registry rule

`connectors/connector_registry.csv` is the single authoritative connector
registry unless the architecture is deliberately migrated to another format.

An empty registry is invalid when connector execution tests require at least one
registered connector.
