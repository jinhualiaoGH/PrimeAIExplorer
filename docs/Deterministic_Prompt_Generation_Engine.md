# Phase B2.6 — Deterministic Prompt Generation Engine

B2.6 converts deterministic B2.5 dataset cases into model-ready prompts with
cryptographic identities and explicit response contracts.

## Operations

```text
prompt.template.list
prompt.template.describe
prompt.generate
prompt.batch
```

## Prompt template configuration

```json
{
  "template_id": "prime-gap-json-v1",
  "template_version": "1.0.0",
  "title": "Prime-gap continuation JSON prompt",
  "system_template": "You are participating in a controlled numerical continuation experiment. Follow the response format exactly.",
  "user_template": "You are given a sequence of consecutive prime gaps.\n\nObservation window size: {observation_count}\n\nObserved gaps:\n{observed_values}\n\nPredict the next prime gap.\n\nReturn JSON only using this exact structure:\n\n{response_schema}",
  "response_schema": {
    "prediction": "<integer>",
    "confidence": "<integer from 0 to 100>",
    "explanation": "<brief explanation>"
  }
}
```

Required user-template placeholders:

```text
{observation_count}
{observed_values}
```

Other supported placeholders include:

```text
{dataset_id}
{case_id}
{case_index}
{sequence_id}
{start_index}
{target_start_index}
{end_index}
{target_count}
{response_schema}
```

## Ground-truth isolation

Normal prompt generation hides the target:

```json
{
  "operation": "prompt.generate",
  "dataset_id": "prime-gap-next-w64",
  "case_index": 0,
  "template_id": "prime-gap-json-v1"
}
```

For internal auditing only:

```json
{
  "operation": "prompt.generate",
  "dataset_id": "prime-gap-next-w64",
  "case_index": 0,
  "template_id": "prime-gap-json-v1",
  "include_ground_truth": true
}
```

## Identity chain

```text
Sequence descriptor identity
          ↓
Dataset identity
          ↓
Case identity
          ↓
Template identity
          ↓
Prompt identity
```

The prompt SHA-256 covers the rendered system message, rendered user message,
response schema, dataset identity, case identity, and template identity.
