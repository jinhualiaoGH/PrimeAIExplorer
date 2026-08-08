from dataclasses import replace

import pytest

from experimental_campaign import (
    AttemptOutcome,
    CampaignExecutionPlanner,
    CampaignExecutionRun,
    CampaignExecutionRuntime,
    CampaignResultAssembler,
    CampaignResultManifest,
    CampaignResultRecord,
    CampaignResultSet,
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
    ProviderTarget,
    ProvenanceLink,
    ScientificProvenance,
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


def build_chain(*, executor=None):
    experiment = ExperimentDefinition(
        experiment_id="EXP-H6-001",
        title="H6 result assembly",
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
            retries_per_trial=1,
            timeout_seconds=30,
        ),
    )
    inputs = build_inputs()
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
            batch_size=3,
            max_parallel_jobs=2,
        ),
    )

    if executor is None:
        executor = lambda job, attempt: AttemptOutcome(
            successful=True,
            response_text='{"prediction": 6}',
            provider_request_id=f"REQ-{job.job_id}",
        )

    run = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=executor,
        run_id="RUN-H6-001",
    )
    return experiment, materialization, plan, run


def assemble(*, executor=None):
    experiment, materialization, plan, run = build_chain(executor=executor)
    return CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )


def test_result_record_from_execution_record():
    _, _, _, run = build_chain()
    record = CampaignResultRecord.from_execution_record(run.records[0])
    assert record.job_id == run.records[0].job_id


def test_result_record_identity_stable():
    _, _, _, run = build_chain()
    a = CampaignResultRecord.from_execution_record(run.records[0])
    b = CampaignResultRecord.from_execution_record(run.records[0])
    assert a.result_sha256 == b.result_sha256


def test_result_record_requires_response_on_success():
    record = CampaignResultRecord.from_execution_record(build_chain()[3].records[0])
    with pytest.raises(ValidationError):
        replace(record, response_text=None)


def test_result_record_rejects_zero_attempt_count():
    record = CampaignResultRecord.from_execution_record(build_chain()[3].records[0])
    with pytest.raises(ValidationError):
        replace(record, attempt_count=0)


def test_result_record_rejects_zero_ordinal():
    record = CampaignResultRecord.from_execution_record(build_chain()[3].records[0])
    with pytest.raises(ValidationError):
        replace(record, ordinal=0)


def test_result_set_count():
    assembly = assemble()
    assert assembly.result_set.result_count == 4


def test_result_set_all_success():
    assembly = assemble()
    assert assembly.result_set.succeeded_count == 4
    assert assembly.result_set.failed_count == 0
    assert assembly.result_set.exhausted_count == 0


def test_result_set_identity_stable():
    assert assemble().result_set.result_set_sha256 == assemble().result_set.result_set_sha256


def test_result_set_id_stable():
    assert assemble().result_set.result_set_id == assemble().result_set.result_set_id


def test_result_set_preserves_experiment_identity():
    experiment, materialization, plan, run = build_chain()
    assembly = CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )
    assert assembly.result_set.experiment_id == experiment.experiment_id
    assert assembly.result_set.experiment_sha256 == experiment.experiment_sha256


def test_result_set_preserves_materialization_identity():
    experiment, materialization, plan, run = build_chain()
    assembly = CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )
    assert assembly.result_set.materialization_sha256 == materialization.materialization_sha256


def test_result_set_preserves_plan_identity():
    experiment, materialization, plan, run = build_chain()
    assembly = CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )
    assert assembly.result_set.plan_sha256 == plan.plan_sha256


def test_result_set_preserves_run_identity():
    experiment, materialization, plan, run = build_chain()
    assembly = CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )
    assert assembly.result_set.run_sha256 == run.run_sha256


def test_assembler_requires_experiment():
    _, materialization, plan, run = build_chain()
    with pytest.raises(ValidationError):
        CampaignResultAssembler().assemble(
            experiment=None,
            materialization=materialization,
            plan=plan,
            run=run,
        )


def test_assembler_requires_materialization():
    experiment, _, plan, run = build_chain()
    with pytest.raises(ValidationError):
        CampaignResultAssembler().assemble(
            experiment=experiment,
            materialization=None,
            plan=plan,
            run=run,
        )


def test_assembler_requires_plan():
    experiment, materialization, _, run = build_chain()
    with pytest.raises(ValidationError):
        CampaignResultAssembler().assemble(
            experiment=experiment,
            materialization=materialization,
            plan=None,
            run=run,
        )


def test_assembler_requires_run():
    experiment, materialization, plan, _ = build_chain()
    with pytest.raises(ValidationError):
        CampaignResultAssembler().assemble(
            experiment=experiment,
            materialization=materialization,
            plan=plan,
            run=None,
        )


def test_assembler_rejects_run_plan_id_mismatch():
    experiment, materialization, plan, run = build_chain()
    bad = replace(run, plan_id="OTHER")
    with pytest.raises(ValidationError):
        CampaignResultAssembler().assemble(
            experiment=experiment,
            materialization=materialization,
            plan=plan,
            run=bad,
        )


def test_assembler_rejects_run_plan_sha_mismatch():
    experiment, materialization, plan, run = build_chain()
    bad = replace(run, plan_sha256="f" * 64)
    with pytest.raises(ValidationError):
        CampaignResultAssembler().assemble(
            experiment=experiment,
            materialization=materialization,
            plan=plan,
            run=bad,
        )


def test_assembler_rejects_missing_run_job():
    experiment, materialization, plan, run = build_chain()
    bad = CampaignExecutionRun(
        run_id=run.run_id,
        plan_id=run.plan_id,
        plan_sha256=run.plan_sha256,
        records=run.records[:-1],
    )
    with pytest.raises(ValidationError):
        CampaignResultAssembler().assemble(
            experiment=experiment,
            materialization=materialization,
            plan=plan,
            run=bad,
        )


def test_provenance_has_chain_links():
    assembly = assemble()
    relations = {link.relation for link in assembly.provenance.links}
    assert {
        "materialized_from",
        "planned_from",
        "executed_from",
        "assembled_from",
        "result_of",
    }.issubset(relations)


def test_provenance_has_one_result_link_per_result():
    assembly = assemble()
    result_links = [
        link for link in assembly.provenance.links
        if link.relation == "result_of"
    ]
    assert len(result_links) == assembly.result_set.result_count


def test_provenance_identity_stable():
    assert assemble().provenance.provenance_sha256 == assemble().provenance.provenance_sha256


def test_provenance_id_stable():
    assert assemble().provenance.provenance_id == assemble().provenance.provenance_id


def test_provenance_link_identity_stable():
    assembly = assemble()
    link = assembly.provenance.links[0]
    assert link.link_sha256 == link.link_sha256


def test_provenance_link_rejects_blank_relation():
    assembly = assemble()
    link = assembly.provenance.links[0]
    with pytest.raises(ValidationError):
        replace(link, relation=" ")


def test_provenance_rejects_duplicate_links():
    assembly = assemble()
    link = assembly.provenance.links[0]
    with pytest.raises(ValidationError):
        ScientificProvenance(
            provenance_id="P",
            experiment_id=assembly.provenance.experiment_id,
            experiment_sha256=assembly.provenance.experiment_sha256,
            materialization_sha256=assembly.provenance.materialization_sha256,
            plan_id=assembly.provenance.plan_id,
            plan_sha256=assembly.provenance.plan_sha256,
            run_id=assembly.provenance.run_id,
            run_sha256=assembly.provenance.run_sha256,
            result_set_id=assembly.provenance.result_set_id,
            result_set_sha256=assembly.provenance.result_set_sha256,
            links=(link, link),
        )


def test_assembly_identity_stable():
    assert assemble().assembly_sha256 == assemble().assembly_sha256


def test_assembly_to_dict():
    payload = assemble().to_dict()
    assert payload["schema_version"] == "h6.0"
    assert "result_set" in payload
    assert "provenance" in payload


def test_manifest_from_assembly():
    assembly = assemble()
    manifest = CampaignResultManifest.from_assembly(
        assembly,
        source="unit-test",
    )
    assert manifest.assembly_sha256 == assembly.assembly_sha256
    assert manifest.result_count == assembly.result_set.result_count


def test_manifest_identity_stable():
    assembly = assemble()
    a = CampaignResultManifest.from_assembly(assembly, source="unit-test")
    b = CampaignResultManifest.from_assembly(assembly, source="unit-test")
    assert a.manifest_sha256 == b.manifest_sha256


def test_manifest_rejects_bad_terminal_counts():
    manifest = CampaignResultManifest.from_assembly(
        assemble(),
        source="unit-test",
    )
    with pytest.raises(ValidationError):
        replace(manifest, succeeded_count=manifest.succeeded_count - 1)


def test_manifest_rejects_bad_result_digest_count():
    manifest = CampaignResultManifest.from_assembly(
        assemble(),
        source="unit-test",
    )
    with pytest.raises(ValidationError):
        replace(manifest, result_sha256s=manifest.result_sha256s[:-1])


def test_failure_result_preserved():
    def executor(job, attempt):
        return AttemptOutcome(
            successful=False,
            error_class="BadRequest",
            error_message="bad",
            retryable=False,
        )

    assembly = assemble(executor=executor)
    assert assembly.result_set.failed_count == 4
    assert all(item.error_class == "BadRequest" for item in assembly.result_set.results)


def test_exhausted_result_preserved():
    def executor(job, attempt):
        return AttemptOutcome(
            successful=False,
            error_class="Transient",
            error_message="retry",
            retryable=True,
        )

    assembly = assemble(executor=executor)
    assert assembly.result_set.exhausted_count == 4
    assert all(item.attempt_count == 2 for item in assembly.result_set.results)


def test_result_changes_when_response_changes():
    a = assemble(
        executor=lambda job, attempt: AttemptOutcome(
            successful=True,
            response_text="one",
        )
    )
    b = assemble(
        executor=lambda job, attempt: AttemptOutcome(
            successful=True,
            response_text="two",
        )
    )
    assert a.result_set.result_set_sha256 != b.result_set.result_set_sha256


def test_provenance_changes_when_result_changes():
    a = assemble(
        executor=lambda job, attempt: AttemptOutcome(
            successful=True,
            response_text="one",
        )
    )
    b = assemble(
        executor=lambda job, attempt: AttemptOutcome(
            successful=True,
            response_text="two",
        )
    )
    assert a.provenance.provenance_sha256 != b.provenance.provenance_sha256


def test_result_order_is_plan_ordinal_order():
    assembly = assemble()
    ordinals = [item.ordinal for item in assembly.result_set.results]
    assert ordinals == sorted(ordinals)


def test_result_job_ids_match_run():
    experiment, materialization, plan, run = build_chain()
    assembly = CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )
    assert {item.job_id for item in assembly.result_set.results} == {
        item.job_id for item in run.records
    }


def test_result_case_ids_match_plan():
    experiment, materialization, plan, run = build_chain()
    assembly = CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
    )
    cases = {job.job_id: job.case_id for job in plan.jobs}
    assert all(cases[item.job_id] == item.case_id for item in assembly.result_set.results)


def test_result_metadata_contains_execution_record_sha():
    assembly = assemble()
    assert all(
        "execution_record_sha256" in item.metadata
        for item in assembly.result_set.results
    )


def test_assembly_metadata_preserved_in_result_set():
    experiment, materialization, plan, run = build_chain()
    assembly = CampaignResultAssembler().assemble(
        experiment=experiment,
        materialization=materialization,
        plan=plan,
        run=run,
        metadata={"campaign": "H6"},
    )
    assert assembly.result_set.metadata == {"campaign": "H6"}


def test_manifest_to_dict_summary():
    manifest = CampaignResultManifest.from_assembly(
        assemble(),
        source="unit-test",
    )
    payload = manifest.to_dict()
    assert payload["schema_version"] == "h6.0"
    assert payload["result_count"] == 4


def test_empty_campaign_assembly():
    experiment = ExperimentDefinition(
        experiment_id="EXP-H6-EMPTY",
        title="H6 empty",
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
    assert assembly.result_set.result_count == 0
    assert len(assembly.provenance.links) == 4
