from dataclasses import replace
import json

import pytest

from experimental_campaign import (
    AnalysisDisposition,
    AttemptOutcome,
    BehavioralAnalysisOutcome,
    CampaignAnalysisEngine,
    CampaignExecutionPlanner,
    CampaignExecutionRuntime,
    CampaignObservatoryPublisher,
    CampaignResultAssembler,
    DatasetDescriptor,
    DatasetRegistry,
    DatasetSpec,
    ExperimentDefinition,
    ExperimentMaterializer,
    ExperimentalInputRegistry,
    FrozenGBehavioralAdapter,
    PlanningPolicy,
    PromptRegistry,
    PromptSpec,
    PromptSuite,
    PromptTemplate,
    ProviderTarget,
    ScientificIntegrationManifest,
    SourceRecord,
    build_scientific_integration_record,
)
from kernel.exceptions import ValidationError


class GResult:
    def __init__(
        self,
        *,
        disposition,
        score=None,
        confidence=None,
        parsed_value=None,
        evaluator_id="g4.test",
        metrics=None,
    ):
        self.disposition = disposition
        self.score = score
        self.confidence = confidence
        self.parsed_value = parsed_value
        self.evaluator_id = evaluator_id
        self.metrics = metrics or {}


def build_assembly():
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
    inputs = registry.resolve(
        dataset_id="prime-gaps",
        dataset_version="1",
        prompt_suite_id="suite",
        prompt_suite_version="1",
    )
    experiment = ExperimentDefinition(
        experiment_id="EXP-H8-001",
        title="H8 integration",
        task_family="prime-gap",
        dataset_spec=DatasetSpec("prime-gaps", "1"),
        prompt_spec=PromptSpec("prime-gap-json", "1"),
        evaluation_contract_id="numeric-exact",
        provider_targets=(
            ProviderTarget("openai", "gpt-a"),
            ProviderTarget("deepseek", "ds-a"),
        ),
    )
    materialization = ExperimentMaterializer().materialize(
        experiment=experiment,
        inputs=inputs,
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
        prediction = 6 if job.provider == "openai" else 8
        return AttemptOutcome(
            successful=True,
            response_text=json.dumps(
                {"prediction": prediction, "confidence": 80}
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


def g_evaluator(result):
    payload = json.loads(result.response_text)
    prediction = payload["prediction"]
    passed = prediction == 6
    return GResult(
        disposition="passed" if passed else "failed",
        score=1.0 if passed else 0.0,
        confidence=payload["confidence"],
        parsed_value=prediction,
        metrics={"accuracy": 1.0 if passed else 0.0},
    )


def build_report():
    assembly = build_assembly()
    adapter = FrozenGBehavioralAdapter(
        evaluator=g_evaluator,
        evaluator_id="g4.semantic-router",
    )
    report = CampaignAnalysisEngine().analyze(
        assembly=assembly,
        analyzer=adapter,
    )
    return assembly, adapter, report


def test_adapter_requires_callable():
    with pytest.raises(ValidationError):
        FrozenGBehavioralAdapter(evaluator=123)


def test_adapter_accepts_mapping():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "score": 1,
            "confidence": 90,
            "prediction": 6,
            "metrics": {"accuracy": 1},
        },
    )
    result = build_assembly().result_set.results[0]
    outcome = adapter(result)
    assert outcome.disposition == AnalysisDisposition.PASSED


def test_adapter_object_result():
    adapter = FrozenGBehavioralAdapter(evaluator=g_evaluator)
    outcome = adapter(build_assembly().result_set.results[0])
    assert isinstance(outcome, BehavioralAnalysisOutcome)


def test_adapter_maps_passed():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {"disposition": "passed"},
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.disposition == AnalysisDisposition.PASSED


def test_adapter_maps_failed():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {"disposition": "failed"},
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.disposition == AnalysisDisposition.FAILED


def test_adapter_maps_indeterminate():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {"disposition": "indeterminate"},
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.disposition == AnalysisDisposition.INDETERMINATE


def test_adapter_maps_provider_error():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {"disposition": "provider_error"},
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.disposition == AnalysisDisposition.PROVIDER_ERROR


def test_adapter_rejects_unknown_disposition():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {"disposition": "mystery"},
    )
    with pytest.raises(ValidationError):
        adapter(build_assembly().result_set.results[0])


def test_adapter_normalizes_percent_confidence():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "confidence": 80,
        },
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.confidence == 0.8


def test_adapter_preserves_fraction_confidence():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "confidence": 0.8,
        },
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.confidence == 0.8


def test_adapter_rejects_bad_confidence():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "confidence": 101,
        },
    )
    with pytest.raises(ValidationError):
        adapter(build_assembly().result_set.results[0])


def test_adapter_score():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "score": 0.75,
        },
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.score == 0.75


def test_adapter_prediction_alias():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "prediction": 6,
        },
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.parsed_value == 6


def test_adapter_metrics():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "metrics": {"b": 2, "a": 1},
        },
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.metrics == {"a": 1.0, "b": 2.0}


def test_adapter_metadata_identifies_bridge():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {"disposition": "passed"},
        evaluator_id="g4.router",
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.metadata["adapter"] == "FrozenGBehavioralAdapter"
    assert outcome.metadata["phase_g_contract"] == "g4.router"


def test_h7_report_from_g_adapter():
    _, _, report = build_report()
    assert report.observation_count == 4
    assert len(report.summaries) == 2


def test_h7_report_openai_pass():
    _, _, report = build_report()
    summary = next(item for item in report.summaries if item.provider == "openai")
    assert summary.pass_rate == 1.0


def test_h7_report_deepseek_fail():
    _, _, report = build_report()
    summary = next(item for item in report.summaries if item.provider == "deepseek")
    assert summary.pass_rate == 0.0


def test_integration_record():
    assembly, adapter, report = build_report()
    record = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    assert record.analysis_report_sha256 == report.report_sha256


def test_integration_identity_stable():
    assembly, adapter, report = build_report()
    a = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    b = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    assert a.integration_sha256 == b.integration_sha256


def test_integration_id_stable():
    assembly, adapter, report = build_report()
    a = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    b = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    assert a.integration_id == b.integration_id


def test_integration_rejects_result_set_mismatch():
    assembly, adapter, report = build_report()
    bad = replace(report, result_set_id="OTHER")
    with pytest.raises(ValidationError):
        build_scientific_integration_record(
            assembly=assembly,
            analysis_report=bad,
            adapter_id=adapter.evaluator_id,
        )


def test_integration_rejects_provenance_mismatch():
    assembly, adapter, report = build_report()
    bad = replace(report, provenance_sha256="f" * 64)
    with pytest.raises(ValidationError):
        build_scientific_integration_record(
            assembly=assembly,
            analysis_report=bad,
            adapter_id=adapter.evaluator_id,
        )


def test_integration_metadata():
    assembly, adapter, report = build_report()
    record = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
        metadata={"campaign": "H8"},
    )
    assert record.metadata == {"campaign": "H8"}


def observatory_publisher(report, integration):
    return {
        "snapshot_id": f"OBS-{report.report_id}",
        "report_sha256": report.report_sha256,
        "integration_sha256": integration.integration_sha256,
        "provider_models": [
            f"{item.provider}/{item.model}"
            for item in report.summaries
        ],
    }


def test_publisher_requires_callable():
    with pytest.raises(ValidationError):
        CampaignObservatoryPublisher(publisher=123)


def test_publication():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publication = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    assert publication.report_sha256 == report.report_sha256


def test_publication_identity_stable():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publisher = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    )
    a = publisher.publish(
        analysis_report=report,
        integration=integration,
    )
    b = publisher.publish(
        analysis_report=report,
        integration=integration,
    )
    assert a.publication_sha256 == b.publication_sha256


def test_publication_id_stable():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publisher = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    )
    a = publisher.publish(analysis_report=report, integration=integration)
    b = publisher.publish(analysis_report=report, integration=integration)
    assert a.publication_id == b.publication_id


def test_publication_rejects_report_id_mismatch():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    bad = replace(integration, analysis_report_id="OTHER")
    with pytest.raises(ValidationError):
        CampaignObservatoryPublisher(
            publisher=observatory_publisher,
        ).publish(
            analysis_report=report,
            integration=bad,
        )


def test_publication_canonicalizes_mapping_order():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    a = CampaignObservatoryPublisher(
        publisher=lambda r, i: {"b": 2, "a": 1},
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    b = CampaignObservatoryPublisher(
        publisher=lambda r, i: {"a": 1, "b": 2},
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    assert a.publication_sha256 == b.publication_sha256


def test_publication_metadata():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publication = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
        metadata={"layer": "G8"},
    ).publish(
        analysis_report=report,
        integration=integration,
        metadata={"campaign": "H8"},
    )
    assert publication.metadata == {
        "campaign": "H8",
        "layer": "G8",
    }


def test_manifest_build():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publication = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    manifest = ScientificIntegrationManifest.build(
        integration=integration,
        publication=publication,
        source="unit-test",
    )
    assert manifest.publication_sha256 == publication.publication_sha256


def test_manifest_identity_stable():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publication = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    a = ScientificIntegrationManifest.build(
        integration=integration,
        publication=publication,
        source="unit-test",
    )
    b = ScientificIntegrationManifest.build(
        integration=integration,
        publication=publication,
        source="unit-test",
    )
    assert a.manifest_sha256 == b.manifest_sha256


def test_manifest_rejects_bad_integration_id():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publication = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    bad = replace(publication, integration_id="OTHER")
    with pytest.raises(ValidationError):
        ScientificIntegrationManifest.build(
            integration=integration,
            publication=bad,
            source="unit-test",
        )


def test_manifest_to_dict():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publication = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    manifest = ScientificIntegrationManifest.build(
        integration=integration,
        publication=publication,
        source="unit-test",
    )
    assert manifest.to_dict()["schema_version"] == "h8.0"


def test_end_to_end_hash_chain_lengths():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publication = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    manifest = ScientificIntegrationManifest.build(
        integration=integration,
        publication=publication,
        source="unit-test",
    )
    assert len(integration.integration_sha256) == 64
    assert len(publication.publication_sha256) == 64
    assert len(manifest.manifest_sha256) == 64


def test_adapter_uses_status_alias():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {"status": "passed"},
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.disposition == AnalysisDisposition.PASSED


def test_adapter_rejects_non_mapping_metrics():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "metrics": ["bad"],
        },
    )
    with pytest.raises(ValidationError):
        adapter(build_assembly().result_set.results[0])


def test_adapter_rejects_non_numeric_score():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {
            "disposition": "passed",
            "score": "bad",
        },
    )
    with pytest.raises(ValidationError):
        adapter(build_assembly().result_set.results[0])


def test_adapter_custom_metadata():
    adapter = FrozenGBehavioralAdapter(
        evaluator=lambda result: {"disposition": "passed"},
        metadata={"contract_version": "G4"},
    )
    outcome = adapter(build_assembly().result_set.results[0])
    assert outcome.metadata["contract_version"] == "G4"


def test_publication_to_dict():
    assembly, adapter, report = build_report()
    integration = build_scientific_integration_record(
        assembly=assembly,
        analysis_report=report,
        adapter_id=adapter.evaluator_id,
    )
    publication = CampaignObservatoryPublisher(
        publisher=observatory_publisher,
    ).publish(
        analysis_report=report,
        integration=integration,
    )
    assert publication.to_dict()["schema_version"] == "h8.0"
