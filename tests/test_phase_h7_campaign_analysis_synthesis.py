from dataclasses import replace
import json

import pytest

from experimental_campaign import (
    AnalysisDisposition,
    AttemptOutcome,
    BehavioralAnalysisOutcome,
    CampaignAnalysisEngine,
    CampaignAnalysisManifest,
    CampaignExecutionPlanner,
    CampaignExecutionRuntime,
    CampaignResultAssembler,
    DatasetDescriptor,
    DatasetRegistry,
    DatasetSpec,
    ExperimentDefinition,
    ExperimentMaterializer,
    ExperimentalInputRegistry,
    PlanningPolicy,
    PromptRegistry,
    PromptSpec,
    PromptSuite,
    PromptTemplate,
    ProviderModelSummary,
    ProviderTarget,
    SourceRecord,
    TrialPolicy,
)
from kernel.exceptions import ValidationError


def build_inputs():
    dataset = DatasetDescriptor(
        "prime-gaps",
        "1",
        "repository://prime-gaps/v1",
        "jsonl",
    )
    prompt = PromptTemplate(
        "prime-gap-json",
        "1",
        "Observed: {gaps}. Predict next.",
    )
    registry = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset,)),
        prompts=PromptRegistry(
            prompts=(prompt,),
            suites=(PromptSuite("suite", "1", ("prime-gap-json@1",)),),
        ),
    )
    return registry.resolve(
        dataset_id="prime-gaps",
        dataset_version="1",
        prompt_suite_id="suite",
        prompt_suite_version="1",
    )


def build_assembly(*, fail_provider=None):
    experiment = ExperimentDefinition(
        experiment_id="EXP-H7-001",
        title="H7 analysis",
        task_family="prime-gap",
        dataset_spec=DatasetSpec("prime-gaps", "1"),
        prompt_spec=PromptSpec("prime-gap-json", "1"),
        evaluation_contract_id="numeric-exact",
        provider_targets=(
            ProviderTarget("openai", "gpt-a"),
            ProviderTarget("deepseek", "ds-a"),
        ),
        trial_policy=TrialPolicy(
            repetitions=1,
            retries_per_trial=0,
        ),
    )
    materialization = ExperimentMaterializer().materialize(
        experiment=experiment,
        inputs=build_inputs(),
        records=(
            SourceRecord("R1", {"gaps": "2 4 2 6"}),
            SourceRecord("R2", {"gaps": "6 4 2 10"}),
        ),
    )
    plan = CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
        planning_policy=PlanningPolicy(
            batch_size=4,
            max_parallel_jobs=2,
        ),
    )

    def executor(job, attempt):
        if fail_provider == job.provider:
            return AttemptOutcome(
                successful=False,
                error_class="ProviderError",
                error_message="simulated",
                retryable=False,
            )
        value = 6 if job.provider == "openai" else 8
        return AttemptOutcome(
            successful=True,
            response_text=json.dumps(
                {"prediction": value, "confidence": 80}
            ),
            provider_request_id=f"REQ-{job.job_id}",
        )

    run = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=executor,
    )
    return CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )


def analyzer(result):
    payload = json.loads(result.response_text)
    prediction = payload["prediction"]
    passed = prediction == 6
    return BehavioralAnalysisOutcome(
        disposition=(
            AnalysisDisposition.PASSED
            if passed
            else AnalysisDisposition.FAILED
        ),
        score=1.0 if passed else 0.0,
        confidence=payload["confidence"] / 100.0,
        parsed_value=prediction,
        evaluator_id="h7.test.numeric-exact",
        metrics={
            "accuracy": 1.0 if passed else 0.0,
        },
    )


def test_outcome_accepts_pass():
    value = BehavioralAnalysisOutcome(
        disposition=AnalysisDisposition.PASSED,
    )
    assert value.disposition == AnalysisDisposition.PASSED


def test_outcome_rejects_bad_confidence():
    with pytest.raises(ValidationError):
        BehavioralAnalysisOutcome(
            disposition=AnalysisDisposition.PASSED,
            confidence=1.1,
        )


def test_outcome_rejects_non_numeric_metric():
    with pytest.raises(ValidationError):
        BehavioralAnalysisOutcome(
            disposition=AnalysisDisposition.PASSED,
            metrics={"accuracy": "bad"},
        )


def test_engine_requires_assembly():
    with pytest.raises(ValidationError):
        CampaignAnalysisEngine().analyze(
            assembly=None,
            analyzer=analyzer,
        )


def test_engine_requires_callable_analyzer():
    with pytest.raises(ValidationError):
        CampaignAnalysisEngine().analyze(
            assembly=build_assembly(),
            analyzer=123,
        )


def test_report_observation_count():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    assert report.observation_count == 4


def test_report_has_two_provider_model_summaries():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    assert len(report.summaries) == 2


def test_openai_summary_passes():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    summary = next(item for item in report.summaries if item.provider == "openai")
    assert summary.passed_count == 2
    assert summary.failed_count == 0
    assert summary.pass_rate == 1.0


def test_deepseek_summary_fails_semantically():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    summary = next(item for item in report.summaries if item.provider == "deepseek")
    assert summary.failed_count == 2
    assert summary.passed_count == 0
    assert summary.pass_rate == 0.0


def test_mean_score():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    openai = next(item for item in report.summaries if item.provider == "openai")
    deepseek = next(item for item in report.summaries if item.provider == "deepseek")
    assert openai.mean_score == 1.0
    assert deepseek.mean_score == 0.0


def test_mean_confidence():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    assert all(item.mean_confidence == 0.8 for item in report.summaries)


def test_aggregated_metric():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    openai = next(item for item in report.summaries if item.provider == "openai")
    assert openai.metrics["accuracy"] == 1.0


def test_provider_failure_becomes_provider_error_without_analyzer_call():
    calls = []

    def tracking(result):
        calls.append(result.provider)
        return analyzer(result)

    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(fail_provider="deepseek"),
        analyzer=tracking,
    )
    assert calls == ["openai", "openai"]
    deepseek = next(item for item in report.summaries if item.provider == "deepseek")
    assert deepseek.provider_error_count == 2


def test_provider_error_summary_rate():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(fail_provider="deepseek"),
        analyzer=analyzer,
    )
    deepseek = next(item for item in report.summaries if item.provider == "deepseek")
    assert deepseek.provider_error_rate == 1.0


def test_analyzer_must_return_outcome():
    with pytest.raises(ValidationError):
        CampaignAnalysisEngine().analyze(
            assembly=build_assembly(),
            analyzer=lambda result: "bad",
        )


def test_report_identity_stable():
    assembly = build_assembly()
    a = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    b = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    assert a.report_sha256 == b.report_sha256


def test_report_id_stable():
    assembly = build_assembly()
    a = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    b = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    assert a.report_id == b.report_id


def test_analysis_record_identity_stable():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    assert report.analyses[0].analysis_sha256 == report.analyses[0].analysis_sha256


def test_analysis_preserves_result_identity():
    assembly = build_assembly()
    report = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    by_id = {item.result_id: item for item in assembly.result_set.results}
    assert all(
        item.result_sha256 == by_id[item.result_id].result_sha256
        for item in report.analyses
    )


def test_analysis_preserves_provider_model():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    assert {(item.provider, item.model) for item in report.analyses} == {
        ("openai", "gpt-a"),
        ("deepseek", "ds-a"),
    }


def test_report_preserves_result_set_identity():
    assembly = build_assembly()
    report = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    assert report.result_set_id == assembly.result_set.result_set_id
    assert report.result_set_sha256 == assembly.result_set.result_set_sha256


def test_report_preserves_provenance_identity():
    assembly = build_assembly()
    report = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    assert report.provenance_sha256 == assembly.provenance.provenance_sha256


def test_report_metadata_preserved():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
        metadata={"campaign": "H7"},
    )
    assert report.metadata == {"campaign": "H7"}


def test_report_to_dict():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    payload = report.to_dict()
    assert payload["schema_version"] == "h7.0"
    assert payload["observation_count"] == 4


def test_summary_pass_rate_empty():
    value = ProviderModelSummary(
        provider="p",
        model="m",
        observation_count=0,
        passed_count=0,
        failed_count=0,
        indeterminate_count=0,
        provider_error_count=0,
        mean_score=None,
        mean_confidence=None,
    )
    assert value.pass_rate is None


def test_summary_rejects_bad_counts():
    with pytest.raises(ValidationError):
        ProviderModelSummary(
            provider="p",
            model="m",
            observation_count=2,
            passed_count=1,
            failed_count=0,
            indeterminate_count=0,
            provider_error_count=0,
            mean_score=None,
            mean_confidence=None,
        )


def test_summary_rejects_bad_mean_confidence():
    with pytest.raises(ValidationError):
        ProviderModelSummary(
            provider="p",
            model="m",
            observation_count=1,
            passed_count=1,
            failed_count=0,
            indeterminate_count=0,
            provider_error_count=0,
            mean_score=1.0,
            mean_confidence=2.0,
        )


def test_manifest_from_report():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    manifest = CampaignAnalysisManifest.from_report(
        report,
        source="unit-test",
    )
    assert manifest.report_sha256 == report.report_sha256
    assert manifest.observation_count == report.observation_count


def test_manifest_identity_stable():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    a = CampaignAnalysisManifest.from_report(report, source="unit-test")
    b = CampaignAnalysisManifest.from_report(report, source="unit-test")
    assert a.manifest_sha256 == b.manifest_sha256


def test_manifest_provider_models():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    manifest = CampaignAnalysisManifest.from_report(report, source="unit-test")
    assert manifest.provider_models == (
        "deepseek/ds-a",
        "openai/gpt-a",
    )


def test_manifest_rejects_bad_analysis_count():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    manifest = CampaignAnalysisManifest.from_report(report, source="unit-test")
    with pytest.raises(ValidationError):
        replace(
            manifest,
            observation_count=manifest.observation_count + 1,
        )


def test_manifest_rejects_duplicate_provider_models():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    manifest = CampaignAnalysisManifest.from_report(report, source="unit-test")
    with pytest.raises(ValidationError):
        replace(
            manifest,
            provider_models=("openai/gpt-a", "openai/gpt-a"),
        )


def test_manifest_to_dict():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    manifest = CampaignAnalysisManifest.from_report(report, source="unit-test")
    payload = manifest.to_dict()
    assert payload["schema_version"] == "h7.0"
    assert payload["observation_count"] == 4


def test_indeterminate_disposition_summary():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=lambda result: BehavioralAnalysisOutcome(
            disposition=AnalysisDisposition.INDETERMINATE,
            evaluator_id="indeterminate",
        ),
    )
    assert all(item.indeterminate_count == 2 for item in report.summaries)


def test_partial_metric_aggregation():
    calls = {"n": 0}

    def partial(result):
        calls["n"] += 1
        metrics = {"x": 1.0} if calls["n"] % 2 else {}
        return BehavioralAnalysisOutcome(
            disposition=AnalysisDisposition.PASSED,
            metrics=metrics,
        )

    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=partial,
    )
    values = [summary.metrics.get("x") for summary in report.summaries]
    assert all(value == 1.0 for value in values)


def test_different_analyzer_changes_report_identity():
    assembly = build_assembly()
    a = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    b = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=lambda result: BehavioralAnalysisOutcome(
            disposition=AnalysisDisposition.PASSED,
            evaluator_id="all-pass",
        ),
    )
    assert a.report_sha256 != b.report_sha256


def test_different_result_assembly_changes_report_identity():
    a = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    b = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(fail_provider="deepseek"),
        analyzer=analyzer,
    )
    assert a.report_sha256 != b.report_sha256


def test_empty_campaign_report():
    experiment = ExperimentDefinition(
        experiment_id="EXP-H7-EMPTY",
        title="H7 empty",
        task_family="prime-gap",
        dataset_spec=DatasetSpec("prime-gaps", "1"),
        prompt_spec=PromptSpec("prime-gap-json", "1"),
        evaluation_contract_id="numeric-exact",
        provider_targets=(ProviderTarget("openai", "gpt-a"),),
    )
    materialization = ExperimentMaterializer().materialize(
        experiment=experiment,
        inputs=build_inputs(),
        records=(),
    )
    plan = CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
    )
    run = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=lambda job, attempt: AttemptOutcome(
            successful=True,
            response_text="ok",
        ),
    )
    assembly = CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )
    report = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=analyzer,
    )
    assert report.observation_count == 0
    assert report.summaries == ()


def test_provider_error_outcome_evaluator_id():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(fail_provider="deepseek"),
        analyzer=analyzer,
    )
    errors = [
        item for item in report.analyses
        if item.provider == "deepseek"
    ]
    assert all(
        item.outcome.evaluator_id == "h7.provider-status"
        for item in errors
    )


def test_analysis_metadata_has_planning_coordinates():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    for item in report.analyses:
        assert "target_id" in item.metadata
        assert "lane_id" in item.metadata
        assert "batch_id" in item.metadata


def test_analysis_order_is_deterministic():
    report = CampaignAnalysisEngine().analyze(
        assembly=build_assembly(),
        analyzer=analyzer,
    )
    keys = [
        (item.provider, item.model, item.job_id)
        for item in report.analyses
    ]
    assert keys == sorted(keys)
