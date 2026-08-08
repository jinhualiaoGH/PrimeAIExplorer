# PrimeAIExplorer Phase H7 — Campaign Analysis & Scientific Result Synthesis

## Purpose

Phase H7 consumes the provenance-bearing H6 campaign result assembly and
produces deterministic scientific analysis records and provider/model summaries.

H7 deliberately separates two concerns:

- **Phase H** owns experiment orchestration, evidence, provenance, and synthesis.
- **Phase G** owns behavioral evaluator semantics, metrics, fingerprints, drift,
  and observatory presentation.

H7 therefore introduces a narrow analyzer boundary rather than duplicating
frozen Phase G evaluator logic.

## Analyzer boundary

The analysis engine accepts:

    analyzer(result: CampaignResultRecord) -> BehavioralAnalysisOutcome

This callable may be implemented by:

- a thin adapter over frozen Phase G semantic evaluators,
- a task-specific experimental evaluator,
- an offline replay evaluator,
- a deterministic fixture.

This keeps H7 scientifically explicit and avoids coupling campaign orchestration
to any one evaluator implementation.

## Core components

- `AnalysisDisposition`
- `BehavioralAnalysisOutcome`
- `CampaignAnalysisRecord`
- `ProviderModelSummary`
- `CampaignAnalysisReport`
- `CampaignAnalysisEngine`
- `CampaignAnalysisManifest`
- `BehavioralAnalyzer`

## Provider failures

H7 never sends failed H5/H6 results into a semantic analyzer.

Execution failures and exhausted jobs are converted into
`provider_error` analysis outcomes. This preserves the distinction between:

- model semantic failure, and
- provider/runtime failure.

## Provider/model synthesis

H7 groups analysis records by `(provider, model)` and produces deterministic
summaries containing:

- observation count,
- pass/fail/indeterminate/provider-error counts,
- pass rate,
- provider-error rate,
- mean score,
- mean confidence,
- mean named metrics.

## Identity chain

H7 preserves:

    H6 result_set_sha256
    H6 provenance_sha256
        ↓
    per-result analysis_sha256
        ↓
    provider/model summaries
        ↓
    H7 report_sha256
        ↓
    H7 manifest_sha256

This permits later behavioral observatory exports to prove exactly which
campaign evidence was analyzed.

## Phase G integration direction

A later adapter may translate `CampaignResultRecord` into the frozen G-series
evaluation request contract and translate the G evaluator response into
`BehavioralAnalysisOutcome`.

That adapter should remain thin: H7 must not redefine G1-G8 semantics.

## Next stage

Phase H8 should provide the explicit H↔G integration adapter and scientific
campaign publication/export path.
