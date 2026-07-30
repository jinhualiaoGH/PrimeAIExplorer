# PrimeAIExplorer v1.3 Phase C

## Canonical outputs

```text
experiments/EXP-000003/benchmark/
├── manifest.json
├── cases/
│   ├── public/
│   └── private/
└── prompts/
    └── text/
```

## Public/private separation

Public case JSON contains:

- observation values;
- window size;
- one-based observation and target indices;
- dataset hash;
- case hash.

It does not contain the target value.

Private case JSON contains the same fields plus:

- target;
- answer-key hash.

## Deterministic identity

Given the same:

- dataset hash;
- configuration;
- sampling seed;
- window sizes;
- case count;

the manifest, case IDs, endpoint selections, public case hashes, answer-key hashes,
and prompt hashes are reproducible.

## Blind prompt rule

The default prompt says:

```text
You are given a sequence of consecutive integer values.
```

It does not identify the sequence as prime values and does not contain the hidden target.

## Production corpus

```text
5 window sizes
100 cases per window
500 total cases
```
