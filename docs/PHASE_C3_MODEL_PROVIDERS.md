# PrimeAIExplorer v2.0 Phase C3

C3 adds a provider-neutral `ModelProvider.generate(ModelRequest)` boundary and
a `ProviderExecutor` bridge to the unchanged C2 `CaseExecutionResult` contract.

Adapters: OpenAI Responses API, Anthropic Messages API, Gemini generateContent,
generic/local JSON HTTP, and offline manual JSONL.

Credentials are read only from environment variables at execution time:
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GEMINI_API_KEY`.

For C2 CLI execution, set `PRIMEAIEXPLORER_PROVIDER_CONFIG` to a provider JSON
file and use `--executor model_providers.cli_executor:execute`.

Model names in examples are placeholders because provider model catalogs evolve.
Never commit API keys.
