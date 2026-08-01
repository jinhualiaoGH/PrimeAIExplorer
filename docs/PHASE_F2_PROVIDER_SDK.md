# PrimeAIExplorer v3.0 Phase F2 — Provider SDK Layer

Phase F2 adds provider adapters behind the unified Phase F1 AI gateway.

## Included adapters

- OpenAI Responses API
- Anthropic Messages API
- Google Gemini `generateContent`
- Shared normalized request, response, error, and HTTP transport contracts

## Security

API keys are read only from environment variables:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

No key belongs in Git, JSON configuration, logs, or reproducibility bundles.

## Validation

The Phase F2 tests use an injected fake HTTP transport. They validate request construction,
response normalization, token accounting, endpoint selection, and offline health checks
without making billable network calls.

## Next integration step

Phase F2.2 will connect these adapters to the existing F1 route registry and gateway factory,
then add provider-specific route examples and guarded live smoke tests.
