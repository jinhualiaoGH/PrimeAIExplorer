# PrimeAIExplorer v2.0 Phase E5

Phase E5 introduces immutable scientific reproducibility bundles.

## Capabilities

- Artifact collection from one or more completed pipeline or campaign outputs
- SHA-256 verification for every copied artifact
- Canonical JSON manifests
- Environment, Python, package, and Git provenance capture
- Secret-safe selected environment capture
- Explicit reproduction command recording
- Atomic manifest writes
- Deterministic ZIP packaging
- Tamper detection
- Refusal to overwrite an existing bundle unless explicitly requested

## Bundle layout

```text
bundle_name/
    artifacts/
    environment.json
    reproduce.json
    manifest.json
bundle_name.zip
```

## Security note

Environment variables whose names contain `KEY`, `TOKEN`, `SECRET`, or
`PASSWORD` are never written into the bundle.
