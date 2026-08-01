# Phase B2.3 — Partitioned Gap Sequence Provider

B2.3 exposes a partitioned `uint16` gap repository through the common Sequence
Provider contract.

## Manifest contract

```json
{
  "schema_version": "1.0",
  "repository_id": "primenet-gap-u16-v3",
  "repository_version": "3.0.0",
  "dtype": "uint16",
  "index_origin": 1,
  "partitions": [
    {
      "ordinal": 0,
      "start_index": 1,
      "count": 1000000,
      "path": "gaps_000.npy",
      "sha256": "<optional 64-character digest>"
    }
  ],
  "metadata": {
    "ownership": "one stored prime index owns one outgoing gap"
  }
}
```

B2.3 intentionally uses a neutral JSON manifest. A later PrimeNet connector can
translate the canonical PrimeNet CSV manifest into this contract without
coupling the Sequence API to a repository-specific filename convention.

## Guarantees

- read-only NumPy memory maps;
- strict `uint16` enforcement;
- contiguous mathematical index ranges;
- windows spanning any number of partitions;
- deterministic manifest identity;
- optional per-partition SHA-256 verification;
- bounded LRU mapping cache;
- Windows-safe explicit cleanup.
