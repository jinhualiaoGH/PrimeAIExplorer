# PrimeAIExplorer v2.0 Phase B2.2 — Memory-Mapped Sequence Provider

## Purpose

B2.2 connects the B2.1 sequence contract to persistent NumPy `.npy` files
without loading complete arrays into process memory.

## Data path

```text
NumPy .npy file
      ↓ np.load(..., mmap_mode="r")
read-only np.memmap
      ↓
NpyMemmapSequenceProvider
      ↓
SequenceWindow
      ↓
SequenceExecutionPlugin
      ↓
B1.4 PluginExecutionPipeline
```

## Provider configuration

```json
{
  "provider_type": "numpy_npy_memmap",
  "sequence_id": "prime-value",
  "source_path": "data/prime_values.npy",
  "index_origin": 1,
  "strictly_increasing": true,
  "expected_sha256": "<64-character SHA-256>"
}
```

Relative source paths resolve against `ExecutionContext.project_root`.
Absolute paths are also supported.

## Safety contract

- `.npy` format only;
- `allow_pickle=False`;
- one-dimensional, nonempty numeric arrays only;
- integer, unsigned integer, or floating-point dtype;
- read-only memory mapping;
- explicit boundary validation;
- optional expected SHA-256 verification;
- explicit close lifecycle.

## Determinism

The descriptor contains a file identity with filename, byte length, dtype,
shape, and complete file SHA-256. The absolute host path is deliberately not
included in descriptor metadata, so identical files produce identical
descriptor hashes across machines and repository locations.

## Scope boundary

B2.2 handles one mapped file per provider. Multi-partition repositories,
cross-file windows, repository manifests, cache policy, and PrimeNet-specific
adapters remain later phases.
