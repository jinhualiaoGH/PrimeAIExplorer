# Upgrade Guide — v2.0 Phase B2.2

Required baseline:

```text
2.0.0-phase-b2.1
```

Installed version:

```text
2.0.0-phase-b2.2
```

## Dependency

B2.2 requires NumPy. The installer checks that NumPy can be imported before
changing the destination.

## Compatibility

B2.2 preserves the B2.1 public API. Existing in-memory provider configuration
continues to work. A provider selects memory-mapped behavior by declaring:

```json
"provider_type": "numpy_npy_memmap"
```
