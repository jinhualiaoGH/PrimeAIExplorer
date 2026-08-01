# PrimeAIExplorer v2.0 Phase E3 — Model Invocation Integration

Phase E3 connects the existing Phase C3 `model_providers` abstraction to deterministic pipeline execution.

## Capabilities

- Provider-neutral JSON configuration
- OpenAI, Anthropic, Gemini, generic HTTP, and manual provider adapters
- Normalized response JSONL compatible with the Phase C4 metrics engine
- Request latency, request ID, finish reason, and token-usage metadata
- Atomic response and manifest persistence
- Case-level resume and skip behavior
- Explicit `--force` and `--stop-on-error` controls
- Configuration-only health checks and optional live probes
- Scheduler-ready `invoke_models` command stage

## Architecture

```text
Dataset / prompts
      ↓
model_invocation.cli
      ↓
model_providers registry (Phase C3)
      ↓
OpenAI | Anthropic | Gemini | HTTP | Manual
      ↓
normalized responses.jsonl
      ↓
metrics_engine → report_engine
```

API credentials remain outside the repository and are read from environment variables.
