import pytest

from experimental_campaign import (
    AttemptOutcome,
    CampaignExecutionPlanner,
    CampaignExecutionRuntime,
    CampaignRunManifest,
    DatasetDescriptor,
    DatasetRegistry,
    DatasetSpec,
    ExecutionAttempt,
    ExecutionPolicy,
    ExperimentDefinition,
    ExperimentMaterializer,
    ExperimentalInputRegistry,
    JobExecutionRecord,
    JobExecutionStatus,
    PlanningPolicy,
    PromptRegistry,
    PromptSpec,
    PromptSuite,
    PromptTemplate,
    ProviderTarget,
    SourceRecord,
    TrialPolicy,
)
from kernel.exceptions import ValidationError


def build_inputs():
    dataset = DatasetDescriptor("prime-gaps", "1", "repository://prime-gaps/v1", "jsonl")
    prompt = PromptTemplate("prime-gap-json", "1", "Observed: {gaps}. Predict next.")
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


def build_experiment(*, retries=1, repetitions=1):
    return ExperimentDefinition(
        experiment_id="EXP-H5-001",
        title="H5 runtime",
        task_family="prime-gap",
        dataset_spec=DatasetSpec("prime-gaps", "1"),
        prompt_spec=PromptSpec("prime-gap-json", "1"),
        evaluation_contract_id="numeric-exact",
        provider_targets=(
            ProviderTarget("openai", "gpt-a"),
            ProviderTarget("deepseek", "ds-a"),
        ),
        trial_policy=TrialPolicy(
            repetitions=repetitions,
            retries_per_trial=retries,
            timeout_seconds=30,
        ),
    )


def build_plan(*, retries=1, repetitions=1):
    experiment = build_experiment(retries=retries, repetitions=repetitions)
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
        planning_policy=PlanningPolicy(batch_size=3, max_parallel_jobs=2),
        execution_policy=ExecutionPolicy(max_parallel_jobs=2),
    )
    return plan


def success_executor(job, attempt_index):
    return AttemptOutcome(
        successful=True,
        response_text=f'{{"job":"{job.job_id}","attempt":{attempt_index}}}',
        provider_request_id=f"REQ-{job.job_id}",
    )


def test_attempt_outcome_success():
    assert AttemptOutcome(successful=True, response_text="ok").successful is True


def test_attempt_outcome_rejects_success_with_error():
    with pytest.raises(ValidationError):
        AttemptOutcome(successful=True, response_text="ok", error_class="Error")


def test_attempt_outcome_rejects_nonboolean_retryable():
    with pytest.raises(ValidationError):
        AttemptOutcome(successful=False, retryable=1)


def test_runtime_requires_plan():
    with pytest.raises(ValidationError):
        CampaignExecutionRuntime().execute(plan=None, executor=success_executor)


def test_runtime_requires_callable_executor():
    with pytest.raises(ValidationError):
        CampaignExecutionRuntime().execute(plan=build_plan(), executor=42)


def test_successful_run_job_count():
    result = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    assert result.job_count == 4


def test_successful_run_all_succeeded():
    result = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    assert result.succeeded_count == 4
    assert result.failed_count == 0
    assert result.exhausted_count == 0


def test_successful_run_one_attempt_each():
    result = CampaignExecutionRuntime().execute(plan=build_plan(retries=3), executor=success_executor)
    assert result.total_attempts == result.job_count


def test_run_preserves_plan_identity():
    plan = build_plan()
    result = CampaignExecutionRuntime().execute(plan=plan, executor=success_executor)
    assert result.plan_id == plan.plan_id
    assert result.plan_sha256 == plan.plan_sha256


def test_default_run_id_stable():
    plan = build_plan()
    a = CampaignExecutionRuntime().execute(plan=plan, executor=success_executor)
    b = CampaignExecutionRuntime().execute(plan=plan, executor=success_executor)
    assert a.run_id == b.run_id


def test_custom_run_id_preserved():
    result = CampaignExecutionRuntime().execute(
        plan=build_plan(), executor=success_executor, run_id="RUN-CUSTOM"
    )
    assert result.run_id == "RUN-CUSTOM"


def test_nonretryable_failure_stops_immediately():
    def executor(job, attempt_index):
        return AttemptOutcome(
            successful=False,
            error_class="BadRequest",
            error_message="bad input",
            retryable=False,
        )

    result = CampaignExecutionRuntime().execute(plan=build_plan(retries=3), executor=executor)
    assert result.failed_count == result.job_count
    assert result.total_attempts == result.job_count


def test_retryable_failure_then_success():
    def executor(job, attempt_index):
        if attempt_index == 1:
            return AttemptOutcome(
                successful=False,
                error_class="RateLimit",
                error_message="retry",
                retryable=True,
            )
        return AttemptOutcome(successful=True, response_text="ok")

    result = CampaignExecutionRuntime().execute(plan=build_plan(retries=2), executor=executor)
    assert result.succeeded_count == result.job_count
    assert result.total_attempts == result.job_count * 2


def test_retry_exhaustion():
    def executor(job, attempt_index):
        return AttemptOutcome(
            successful=False,
            error_class="Transient",
            error_message="still failing",
            retryable=True,
        )

    result = CampaignExecutionRuntime().execute(plan=build_plan(retries=2), executor=executor)
    assert result.exhausted_count == result.job_count
    assert result.total_attempts == result.job_count * 3


def test_retry_budget_zero_allows_one_attempt():
    def executor(job, attempt_index):
        return AttemptOutcome(
            successful=False,
            error_class="Transient",
            error_message="retry",
            retryable=True,
        )

    result = CampaignExecutionRuntime().execute(plan=build_plan(retries=0), executor=executor)
    assert result.total_attempts == result.job_count
    assert result.exhausted_count == result.job_count


def test_executor_exception_becomes_nonretryable_failure():
    def executor(job, attempt_index):
        raise RuntimeError("boom")

    result = CampaignExecutionRuntime().execute(plan=build_plan(retries=3), executor=executor)
    assert result.failed_count == result.job_count
    assert result.total_attempts == result.job_count
    assert all(record.terminal_outcome.error_class == "RuntimeError" for record in result.records)


def test_executor_must_return_attempt_outcome():
    def executor(job, attempt_index):
        return "bad"

    with pytest.raises(ValidationError):
        CampaignExecutionRuntime().execute(plan=build_plan(), executor=executor)


def test_record_attempt_indices_contiguous():
    def executor(job, attempt_index):
        if attempt_index < 3:
            return AttemptOutcome(
                successful=False,
                error_class="Transient",
                error_message="retry",
                retryable=True,
            )
        return AttemptOutcome(successful=True, response_text="ok")

    result = CampaignExecutionRuntime().execute(plan=build_plan(retries=2), executor=executor)
    for record in result.records:
        assert [attempt.attempt_index for attempt in record.attempts] == [1, 2, 3]


def test_record_preserves_job_and_case_identity():
    plan = build_plan()
    result = CampaignExecutionRuntime().execute(plan=plan, executor=success_executor)
    jobs = {job.job_id: job for job in plan.jobs}
    assert all(record.job_sha256 == jobs[record.job_id].job_sha256 for record in result.records)
    assert all(record.case_sha256 == jobs[record.job_id].case_sha256 for record in result.records)


def test_record_duration_nonnegative():
    result = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    assert all(record.total_duration_seconds >= 0 for record in result.records)


def test_record_identity_excludes_duration():
    plan = build_plan()
    job = plan.jobs[0]
    outcome = AttemptOutcome(successful=True, response_text="same")
    a = JobExecutionRecord(
        job_id=job.job_id,
        job_sha256=job.job_sha256,
        case_id=job.case_id,
        case_sha256=job.case_sha256,
        status=JobExecutionStatus.SUCCEEDED,
        attempts=(ExecutionAttempt(1, outcome, 0.1),),
        terminal_outcome=outcome,
        total_duration_seconds=0.1,
    )
    b = JobExecutionRecord(
        job_id=job.job_id,
        job_sha256=job.job_sha256,
        case_id=job.case_id,
        case_sha256=job.case_sha256,
        status=JobExecutionStatus.SUCCEEDED,
        attempts=(ExecutionAttempt(1, outcome, 9.9),),
        terminal_outcome=outcome,
        total_duration_seconds=9.9,
    )
    assert a.record_sha256 == b.record_sha256


def test_run_identity_stable_for_same_scientific_results():
    plan = build_plan()
    a = CampaignExecutionRuntime().execute(plan=plan, executor=success_executor)
    b = CampaignExecutionRuntime().execute(plan=plan, executor=success_executor)
    assert a.run_sha256 == b.run_sha256


def test_run_identity_changes_when_response_changes():
    plan = build_plan()
    a = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=lambda job, attempt: AttemptOutcome(successful=True, response_text="one"),
    )
    b = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=lambda job, attempt: AttemptOutcome(successful=True, response_text="two"),
    )
    assert a.run_sha256 != b.run_sha256


def test_run_records_sorted_by_job_id():
    result = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    assert [record.job_id for record in result.records] == sorted(
        record.job_id for record in result.records
    )


def test_run_to_dict_summary():
    result = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    payload = result.to_dict()
    assert payload["schema_version"] == "h5.0"
    assert payload["job_count"] == 4
    assert payload["succeeded_count"] == 4


def test_empty_plan_executes_as_empty_run():
    experiment = build_experiment()
    materialization = ExperimentMaterializer().materialize(
        experiment=experiment,
        inputs=build_inputs(),
        records=(),
    )
    plan = CampaignExecutionPlanner().plan(experiment=experiment, materialization=materialization)
    result = CampaignExecutionRuntime().execute(plan=plan, executor=success_executor)
    assert result.job_count == 0
    assert result.total_attempts == 0


def test_manifest_from_run():
    run = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    manifest = CampaignRunManifest.from_run(run, source="unit-test")
    assert manifest.run_sha256 == run.run_sha256
    assert manifest.job_count == run.job_count


def test_manifest_identity_stable():
    run = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    a = CampaignRunManifest.from_run(run, source="unit-test")
    b = CampaignRunManifest.from_run(run, source="unit-test")
    assert a.manifest_sha256 == b.manifest_sha256


def test_manifest_rejects_bad_status_counts():
    with pytest.raises(ValidationError):
        CampaignRunManifest(
            run_id="R",
            run_sha256="a" * 64,
            plan_id="P",
            plan_sha256="b" * 64,
            job_count=2,
            succeeded_count=1,
            failed_count=0,
            exhausted_count=0,
            total_attempts=1,
            record_sha256s=("c" * 64, "d" * 64),
            source="test",
        )


def test_manifest_rejects_bad_record_count():
    with pytest.raises(ValidationError):
        CampaignRunManifest(
            run_id="R",
            run_sha256="a" * 64,
            plan_id="P",
            plan_sha256="b" * 64,
            job_count=2,
            succeeded_count=2,
            failed_count=0,
            exhausted_count=0,
            total_attempts=2,
            record_sha256s=("c" * 64,),
            source="test",
        )


def test_mixed_terminal_statuses():
    plan = build_plan(retries=1)
    ordered = sorted(job.job_id for job in plan.jobs)
    success_job = ordered[0]
    fail_job = ordered[1]

    def executor(job, attempt_index):
        if job.job_id == success_job:
            return AttemptOutcome(successful=True, response_text="ok")
        if job.job_id == fail_job:
            return AttemptOutcome(
                successful=False,
                error_class="BadRequest",
                error_message="bad",
                retryable=False,
            )
        return AttemptOutcome(
            successful=False,
            error_class="Transient",
            error_message="retry",
            retryable=True,
        )

    result = CampaignExecutionRuntime().execute(plan=plan, executor=executor)
    assert result.succeeded_count == 1
    assert result.failed_count == 1
    assert result.exhausted_count == 2


def test_runtime_metadata_preserved():
    result = CampaignExecutionRuntime().execute(
        plan=build_plan(), executor=success_executor, metadata={"campaign": "H5"}
    )
    assert result.metadata == {"campaign": "H5"}


def test_attempt_metadata_affects_scientific_identity():
    plan = build_plan()
    a = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=lambda job, attempt: AttemptOutcome(
            successful=True, response_text="ok", metadata={"v": 1}
        ),
    )
    b = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=lambda job, attempt: AttemptOutcome(
            successful=True, response_text="ok", metadata={"v": 2}
        ),
    )
    assert a.run_sha256 != b.run_sha256


def test_provider_request_id_affects_scientific_identity():
    plan = build_plan()
    a = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=lambda job, attempt: AttemptOutcome(
            successful=True, response_text="ok", provider_request_id="REQ-1"
        ),
    )
    b = CampaignExecutionRuntime().execute(
        plan=plan,
        executor=lambda job, attempt: AttemptOutcome(
            successful=True, response_text="ok", provider_request_id="REQ-2"
        ),
    )
    assert a.run_sha256 != b.run_sha256


def test_retry_history_affects_scientific_identity():
    plan = build_plan(retries=1)

    def immediate(job, attempt_index):
        return AttemptOutcome(successful=True, response_text="ok")

    def retry_then_success(job, attempt_index):
        if attempt_index == 1:
            return AttemptOutcome(
                successful=False,
                error_class="Transient",
                error_message="retry",
                retryable=True,
            )
        return AttemptOutcome(successful=True, response_text="ok")

    a = CampaignExecutionRuntime().execute(plan=plan, executor=immediate)
    b = CampaignExecutionRuntime().execute(plan=plan, executor=retry_then_success)
    assert a.run_sha256 != b.run_sha256


def test_job_record_metadata_has_planning_coordinates():
    result = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    for record in result.records:
        assert "lane_id" in record.metadata
        assert "batch_id" in record.metadata
        assert "ordinal" in record.metadata


def test_terminal_outcome_matches_last_attempt():
    result = CampaignExecutionRuntime().execute(plan=build_plan(), executor=success_executor)
    assert all(record.terminal_outcome == record.attempts[-1].outcome for record in result.records)


def test_attempt_count_property():
    result = CampaignExecutionRuntime().execute(plan=build_plan(retries=1), executor=success_executor)
    assert all(record.attempt_count == 1 for record in result.records)
