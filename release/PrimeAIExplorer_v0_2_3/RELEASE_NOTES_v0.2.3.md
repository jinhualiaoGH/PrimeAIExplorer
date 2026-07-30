# PrimeAIExplorer v0.2.3 Release Notes

## Native production-response ingestion

v0.2.3 directly reads the original pilot response ledger without a normalization step. Supported inputs include:

- UTF-8 and UTF-8 with BOM
- standard JSON objects and arrays
- aggregate `responses` collections
- CASE-keyed mappings
- NDJSON / JSON Lines
- consecutive JSON objects separated by whitespace
- legacy individual response files

When response objects do not contain `case_id`, the analyzer assigns identifiers from the deterministic pilot prompt order. Prompt files are found recursively, including nested `text` directories.

## Provenance improvements

Every analyzed record now stores:

- `collection_sha256`: SHA-256 of the complete source ledger
- `entry_sha256`: SHA-256 of the canonical individual response entry
- `response_sha256`: backward-compatible alias of `entry_sha256`

## Numerical presentation

Values within numerical tolerance of zero are normalized to exactly `0.0`, eliminating dashboard output such as `-0.000` entropy.
