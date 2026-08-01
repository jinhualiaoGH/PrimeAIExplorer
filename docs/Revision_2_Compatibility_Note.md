# Phase B1.2 Revision 2 Compatibility Note

The verified Phase B1.1 `kernel.serialization` module exports:

- `normalize(value)`
- `canonical_json(value)`
- `stable_sha256(value)`

The first B1.2 package imported `canonical_payload`, which is not part of that
baseline. Revision 2 replaces that dependency with `normalize` and includes an
installer preflight check for all required Phase B1.1 interfaces.

No Phase B1.1 kernel file is modified.
