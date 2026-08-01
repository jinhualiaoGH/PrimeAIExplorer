# Phase B2.4 — PrimeNet Repository Adapter

B2.4 connects the B2.3 partitioned gap provider directly to a PrimeNet-style
CSV repository manifest.

## Provider configuration

```json
{
  "provider_type": "primenet_gap_repository",
  "sequence_id": "prime-gap",
  "repository_root": "E:/PrimeNet/Repository",
  "manifest_path": "gaps_u16_v3/gap_repository_u16_v3_manifest.csv",
  "repository_id": "primenet-gap-u16-v3",
  "repository_version": "3.0.0",
  "index_origin": 1,
  "cache_size": 4,
  "verify_partition_sha256": false
}
```

## Column detection

The adapter recognizes common aliases for:

- partition path;
- gap count;
- mathematical start index;
- partition ordinal;
- SHA-256 digest.

Because PrimeNet manifest schemas may evolve, exact columns can be supplied:

```json
"column_mapping": {
  "path": "gap_file",
  "count": "gap_count",
  "start_index": "first_gap_index",
  "ordinal": "partition_index",
  "sha256": "sha256"
}
```

`path` and `count` are required. `start_index` and `ordinal` can be inferred.

## Architecture

```text
PrimeNet CSV manifest
        ↓
PrimeNetGapRepositoryAdapter
        ↓
Neutral B2.3 GapRepositoryManifest
        ↓
PartitionedGapSequenceProvider
        ↓
Read-only cross-partition windows
```

The adapter writes a generated neutral manifest under:

```text
<repository_root>/.primeaiexplorer/
```

No gap data is copied or rewritten.
