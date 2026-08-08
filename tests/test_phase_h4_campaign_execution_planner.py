import pytest

from experimental_campaign import (
    CampaignExecutionPlan,
    CampaignExecutionPlanner,
    DatasetDescriptor,
    DatasetRegistry,
    DatasetSpec,
    ExecutionPlanManifest,
    ExecutionPolicy,
    ExperimentDefinition,
    ExperimentMaterialization,
    ExperimentMaterializer,
    ExperimentalInputRegistry,
    PlanningPolicy,
    PromptRegistry,
    PromptSpec,
    PromptSuite,
    PromptTemplate,
    ProviderTarget,
    ReproducibilityPolicy,
    SeedPolicy,
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
        "Observed gaps: {gaps}. Predict next.",
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


def build_experiment(*, repetitions=2, retries=1, timeout=30.0):
    return ExperimentDefinition(
        experiment_id="EXP-H4-001",
        title="H4 execution planning",
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
            timeout_seconds=timeout,
        ),
        reproducibility_policy=ReproducibilityPolicy(
            seed_policy=SeedPolicy.DERIVED,
            base_seed=11,
        ),
    )


def build_materialization(*, repetitions=2):
    experiment = build_experiment(repetitions=repetitions)
    materialization = ExperimentMaterializer().materialize(
        experiment=experiment,
        inputs=build_inputs(),
        records=(
            SourceRecord("R2", {"gaps": "6 4 2 10"}),
            SourceRecord("R1", {"gaps": "2 4 2 6"}),
        ),
    )
    return experiment, materialization


def plan(*, repetitions=2, planning_policy=None, execution_policy=None):
    experiment, materialization = build_materialization(repetitions=repetitions)
    return CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
        planning_policy=planning_policy,
        execution_policy=execution_policy,
    )


def test_planning_policy_defaults():
    policy = PlanningPolicy()
    assert policy.batch_size == 32
    assert policy.preserve_provider_affinity is True


def test_planning_policy_rejects_zero_batch_size():
    with pytest.raises(ValidationError):
        PlanningPolicy(batch_size=0)


def test_planning_policy_rejects_zero_parallelism():
    with pytest.raises(ValidationError):
        PlanningPolicy(max_parallel_jobs=0)


def test_planning_policy_rejects_negative_retry_override():
    with pytest.raises(ValidationError):
        PlanningPolicy(retry_budget_override=-1)


def test_planning_policy_rejects_nonpositive_timeout_override():
    with pytest.raises(ValidationError):
        PlanningPolicy(timeout_seconds_override=0)


def test_planner_requires_experiment():
    _, materialization = build_materialization()
    with pytest.raises(ValidationError):
        CampaignExecutionPlanner().plan(
            experiment=None,
            materialization=materialization,
        )


def test_planner_requires_materialization():
    experiment, _ = build_materialization()
    with pytest.raises(ValidationError):
        CampaignExecutionPlanner().plan(
            experiment=experiment,
            materialization=None,
        )


def test_planner_rejects_experiment_mismatch():
    experiment, materialization = build_materialization()
    other = ExperimentDefinition(
        experiment_id="OTHER",
        title=experiment.title,
        task_family=experiment.task_family,
        dataset_spec=experiment.dataset_spec,
        prompt_spec=experiment.prompt_spec,
        evaluation_contract_id=experiment.evaluation_contract_id,
        provider_targets=experiment.provider_targets,
    )
    with pytest.raises(ValidationError):
        CampaignExecutionPlanner().plan(
            experiment=other,
            materialization=materialization,
        )


def test_job_count_matches_materialized_cases():
    result = plan()
    assert result.job_count == 8


def test_job_ids_unique():
    result = plan()
    assert len({job.job_id for job in result.jobs}) == result.job_count


def test_plan_identity_stable():
    assert plan().plan_sha256 == plan().plan_sha256


def test_plan_id_stable():
    assert plan().plan_id == plan().plan_id


def test_custom_plan_id_preserved():
    experiment, materialization = build_materialization()
    result = CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
        plan_id="CUSTOM-PLAN",
    )
    assert result.plan_id == "CUSTOM-PLAN"


def test_default_parallelism_comes_from_execution_policy():
    result = plan(execution_policy=ExecutionPolicy(max_parallel_jobs=3))
    assert result.lane_ids == ("LANE-001", "LANE-002", "LANE-003")


def test_planning_policy_parallelism_overrides_execution_policy():
    result = plan(
        planning_policy=PlanningPolicy(max_parallel_jobs=2),
        execution_policy=ExecutionPolicy(max_parallel_jobs=5),
    )
    assert result.lane_ids == ("LANE-001", "LANE-002")


def test_lane_assignment_round_robins():
    result = plan(
        planning_policy=PlanningPolicy(max_parallel_jobs=2, batch_size=8),
    )
    assert [job.lane_id for job in result.jobs[:4]] == [
        "LANE-001",
        "LANE-002",
        "LANE-001",
        "LANE-002",
    ]


def test_batch_count_respects_batch_size():
    result = plan(
        planning_policy=PlanningPolicy(batch_size=3),
    )
    assert result.batch_count == 3


def test_every_job_referenced_once_by_batches():
    result = plan(planning_policy=PlanningPolicy(batch_size=3))
    referenced = [
        job_id
        for batch in result.batches
        for job_id in batch.job_ids
    ]
    assert len(referenced) == result.job_count
    assert set(referenced) == {job.job_id for job in result.jobs}


def test_retry_budget_defaults_to_trial_policy():
    result = plan()
    assert {job.retry_budget for job in result.jobs} == {1}


def test_retry_budget_override_applied():
    result = plan(
        planning_policy=PlanningPolicy(retry_budget_override=4),
    )
    assert {job.retry_budget for job in result.jobs} == {4}


def test_timeout_defaults_to_trial_policy():
    result = plan()
    assert {job.timeout_seconds for job in result.jobs} == {30.0}


def test_timeout_override_applied():
    result = plan(
        planning_policy=PlanningPolicy(timeout_seconds_override=12),
    )
    assert {job.timeout_seconds for job in result.jobs} == {12.0}


def test_provider_affinity_groups_provider_targets():
    result = plan(
        planning_policy=PlanningPolicy(
            preserve_provider_affinity=True,
            batch_size=8,
        )
    )
    targets = [job.target_id for job in result.jobs]
    assert targets == sorted(targets)


def test_non_affinity_order_is_case_id_order():
    experiment, materialization = build_materialization()
    result = CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
        planning_policy=PlanningPolicy(
            preserve_provider_affinity=False,
            batch_size=8,
        ),
    )
    ordered_case_ids = [job.case_id for job in result.jobs]
    assert ordered_case_ids == sorted(case.case_id for case in materialization.cases)


def test_plan_changes_when_batch_size_changes():
    assert plan(
        planning_policy=PlanningPolicy(batch_size=2)
    ).plan_sha256 != plan(
        planning_policy=PlanningPolicy(batch_size=4)
    ).plan_sha256


def test_plan_changes_when_parallelism_changes():
    assert plan(
        planning_policy=PlanningPolicy(max_parallel_jobs=1)
    ).plan_sha256 != plan(
        planning_policy=PlanningPolicy(max_parallel_jobs=2)
    ).plan_sha256


def test_plan_changes_when_affinity_changes():
    assert plan(
        planning_policy=PlanningPolicy(preserve_provider_affinity=True)
    ).plan_sha256 != plan(
        planning_policy=PlanningPolicy(preserve_provider_affinity=False)
    ).plan_sha256


def test_jobs_preserve_case_provenance():
    experiment, materialization = build_materialization()
    result = CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
    )
    mapping = {case.case_id: case.case_sha256 for case in materialization.cases}
    assert all(mapping[job.case_id] == job.case_sha256 for job in result.jobs)


def test_jobs_preserve_provider_model():
    result = plan()
    pairs = {(job.provider, job.model) for job in result.jobs}
    assert pairs == {
        ("openai", "gpt-a"),
        ("deepseek", "ds-a"),
    }


def test_jobs_preserve_seed():
    experiment, materialization = build_materialization()
    result = CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
    )
    seeds_by_case = {case.case_id: case.seed for case in materialization.cases}
    assert all(seeds_by_case[job.case_id] == job.seed for job in result.jobs)


def test_execution_plan_to_dict_summary():
    result = plan()
    data = result.to_dict()
    assert data["schema_version"] == "h4.0"
    assert data["job_count"] == 8
    assert data["batch_count"] >= 1


def test_execution_plan_rejects_duplicate_job_ids():
    result = plan()
    first = result.jobs[0]
    with pytest.raises(ValidationError):
        CampaignExecutionPlan(
            plan_id="P",
            materialization_sha256=result.materialization_sha256,
            jobs=(first, first),
            batches=result.batches,
            lane_ids=result.lane_ids,
        )


def test_empty_materialization_yields_empty_plan():
    experiment = build_experiment()
    materialization = ExperimentMaterializer().materialize(
        experiment=experiment,
        inputs=build_inputs(),
        records=(),
    )
    result = CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
    )
    assert result.job_count == 0
    assert result.batch_count == 0


def test_manifest_from_plan():
    result = plan()
    manifest = ExecutionPlanManifest.from_plan(
        result,
        source="unit-test",
    )
    assert manifest.plan_sha256 == result.plan_sha256
    assert manifest.job_count == result.job_count
    assert manifest.batch_count == result.batch_count


def test_manifest_identity_stable():
    result = plan()
    a = ExecutionPlanManifest.from_plan(result, source="unit-test")
    b = ExecutionPlanManifest.from_plan(result, source="unit-test")
    assert a.manifest_sha256 == b.manifest_sha256


def test_manifest_rejects_bad_job_count():
    with pytest.raises(ValidationError):
        ExecutionPlanManifest(
            plan_id="P",
            plan_sha256="a" * 64,
            materialization_sha256="b" * 64,
            job_count=2,
            batch_count=0,
            job_ids=("J1",),
            batch_ids=(),
            lane_ids=("LANE-001",),
            source="test",
        )


def test_job_ordinals_are_contiguous():
    result = plan()
    assert [job.ordinal for job in result.jobs] == list(
        range(1, result.job_count + 1)
    )


def test_batch_ordinals_are_contiguous():
    result = plan(planning_policy=PlanningPolicy(batch_size=3))
    assert [batch.ordinal for batch in result.batches] == list(
        range(1, result.batch_count + 1)
    )


def test_plan_metadata_contains_policies():
    result = plan()
    assert "planning_policy" in result.metadata
    assert "execution_policy" in result.metadata


def test_plan_materialization_identity_preserved():
    _, materialization = build_materialization()
    experiment = build_experiment()
    result = CampaignExecutionPlanner().plan(
        experiment=experiment,
        materialization=materialization,
    )
    assert result.materialization_sha256 == materialization.materialization_sha256
