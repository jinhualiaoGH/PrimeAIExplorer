# PrimeAIExplorer Phase H8 — H↔G Scientific Integration & Observatory Publication

## Purpose

Phase H8 closes the first complete PrimeAIExplorer experiment loop.

It connects the Phase H experimental campaign pipeline to the already-frozen
Phase G behavioral evaluation / observatory stack through explicit adapters,
without redefining either subsystem's scientific contracts.

## Architecture

    H1 Experiment Definition
        ↓
    H2 Input Registry
        ↓
    H3 Materialization
        ↓
    H4 Execution Plan
        ↓
    H5 Runtime
        ↓
    H6 Result + Provenance
        ↓
    H7 Analysis
        ↓
    H8 Frozen G Adapter
        ↓
    G-series evaluator semantics
        ↓
    H8 Observatory Publication
        ↓
    G8 / external observatory representation

## Frozen G behavioral adapter

`FrozenGBehavioralAdapter` accepts a callable over an H6
`CampaignResultRecord`.

The callable may be:

- the frozen G4 semantic evaluator router,
- a thin wrapper around `SemanticEvaluatorRegistry`,
- a G-series replay evaluator,
- a compatibility wrapper over an older G evaluation result.

The adapter normalizes a G result into the H7
`BehavioralAnalysisOutcome` contract.

It supports mapping-style or attribute-style G outcomes and normalizes:

- disposition,
- score,
- confidence,
- parsed value / prediction,
- named metrics,
- evaluator identity.

Confidence in either [0,1] or [0,100] is normalized to H7's [0,1] contract.

## No semantic duplication

H8 deliberately does not implement exact-integer, exact-text, structured JSON,
or task-specific semantic evaluators.

Those semantics already belong to frozen Phase G.

H8 only adapts the result contract.

## Scientific integration record

`ScientificIntegrationRecord` binds:

- H6 result-set identity,
- H6 provenance identity,
- H7 analysis-report identity,
- the exact adapter/contract identifier.

This makes the H↔G bridge itself part of the reproducibility chain.

## Observatory publication

`CampaignObservatoryPublisher` accepts a publication callable:

    publisher(analysis_report, integration_record) -> payload

This callable may wrap the frozen G8 observatory builder/exporter.

The returned payload is canonicalized and bound to a
`BehavioralObservatoryPublication` SHA-256 identity.

## Integration manifest

`ScientificIntegrationManifest` binds together:

- H6 result and provenance,
- H7 analysis,
- H8 integration,
- observatory publication,
- publisher identity.

This creates an auditable path from experimental input through final
behavioral-observatory publication.

## Scientific boundary

Phase H owns:
- experiment orchestration,
- runtime evidence,
- provenance,
- result assembly,
- scientific synthesis.

Phase G owns:
- semantic evaluation,
- behavioral metrics,
- fingerprints,
- comparison and drift,
- observatory semantics.

H8 owns only the boundary between them.

## Next direction

After H8, Phase H can be frozen as a complete campaign architecture. A new
Phase I can focus on campaign persistence, release bundles, large-scale
orchestration, and production-grade experiment services.
