# PrimeAIExplorer Phase H2 — Dataset & Prompt Suite Registry

## Purpose

Phase H2 introduces deterministic registries for the scientific inputs consumed
by Phase H experiment definitions.

H2 registers and resolves inputs. It does not execute models or materialize
trial runs.

## Core components

- `DatasetDescriptor`
- `DatasetRegistry`
- `PromptTemplate`
- `PromptSuite`
- `PromptRegistry`
- `ResolvedInputSuite`
- `ExperimentalInputRegistry`

## Dataset identity

A dataset descriptor records:

- dataset ID and version,
- split,
- URI,
- serialization format,
- optional record count,
- optional content SHA-256,
- metadata.

Each descriptor has a deterministic SHA-256 registry identity.

## Prompt identity

A prompt template records:

- prompt ID and version,
- template text,
- optional system prompt,
- JSON mode,
- metadata.

Prompt suites refer to versioned prompts using:

    prompt_id@version

Prompt references are normalized into deterministic order before suite identity
is computed.

## H1 interoperability

Dataset descriptors can emit H1 `DatasetSpec` objects.

Prompt templates can emit H1 `PromptSpec` objects.

Therefore H2 resolves versioned registry entries into the immutable input
contracts required by H1 experiment definitions.

## Conflict rule

Registration is idempotent only when the existing and incoming immutable
descriptors are equal.

A second registration using the same identity key but different content raises
`ValidationError`.

This prevents silent scientific mutation.

## Scientific boundary

    H1 defines experiment identity.
    H2 defines and resolves versioned scientific inputs.
    H3 will materialize concrete experiment cases.

No provider/API calls are made in H2.
