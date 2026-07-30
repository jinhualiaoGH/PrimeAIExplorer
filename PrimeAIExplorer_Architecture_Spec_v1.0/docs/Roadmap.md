# PrimeAIExplorer Roadmap

## Milestone 1 — Architecture inventory

- Review current core modules.
- Review connector registry and loader.
- Identify duplicate ownership.
- Document current execution path.
- Freeze migration boundaries.

## Milestone 2 — Foundation consolidation

- Create one configuration loader.
- Create one plugin registry.
- Define repository adapter.
- Normalize error types.
- Add `pyproject.toml`.

## Milestone 3 — Connector stabilization

- Restore a valid mock connector registry.
- Make registry tests isolated.
- Validate connector capabilities.
- Preserve no-network mock execution.

## Milestone 4 — Sequence SDK

- Stabilize prime-gap plugin.
- Stabilize left-twin plugin.
- Add dataset validation and manifests.
- Add representation adapters.

## Milestone 5 — Evaluation SDK

- Consolidate existing evaluation functions.
- Register metric plugins.
- Add confidence calibration.
- Add sequence-specific structural validity.

## Milestone 6 — Reference experiments

- Rebuild EXP-000001 on the stable platform.
- Rebuild EXP-000002 on the stable platform.
- Compare outputs with pilot evidence.

## Milestone 7 — Stable release

- Full test pass.
- API freeze.
- Developer documentation.
- Reproducible demo.
- PrimeAIExplorer v1.0 release.
