# PrimeValueSequencePlugin — Phase A

Implemented: configuration ownership, canonical PrimeNet partition discovery, numeric ordering, adjacency checks, shape/dtype/range validation, optional full monotonic validation, boundary monotonicity, source count sufficiency, optional manifest SHA-256, and prime structural validity.

`build_dataset()` and `validate_dataset()` deliberately raise `NotImplementedError` until Phase B.

Default dry run checks partition headers and boundaries. The optional full check reads every adjacent value:

```powershell
py .\scripts\dry_run_exp000003.py `
    --full-monotonic-check
```
