import json

import pytest

from experimental_campaign import (
    CampaignManifest,
    CampaignSpec,
    DatasetSpec,
    ExecutionPolicy,
    ExperimentDefinition,
    ExperimentManifest,
    FailurePolicy,
    PromptSpec,
    ProviderTarget,
    ReproducibilityPolicy,
    SeedPolicy,
    TrialPolicy,
    canonical_json,
)
from kernel.exceptions import ValidationError


def target(provider="openai", model="gpt-test", **kwargs):
    return ProviderTarget(provider=provider, model=model, **kwargs)


def experiment(experiment_id="EXP-001", targets=None, repetitions=3, metadata=None):
    return ExperimentDefinition(
        experiment_id=experiment_id,
        title="Prime gap continuation",
        description="Controlled numerical continuation experiment",
        task_family="prime-gap-next-value",
        dataset_spec=DatasetSpec(
            dataset_id="prime-gaps",
            version="1",
            selector={"window": 64},
        ),
        prompt_spec=PromptSpec(
            prompt_id="prime-gap-json",
            version="1",
            template_variables={"format": "json"},
        ),
        evaluation_contract_id="prime-gap.numeric-exact",
        provider_targets=tuple(
            targets
            if targets is not None
            else (
                target("openai", "gpt-test"),
                target("deepseek", "deepseek-test"),
            )
        ),
        trial_policy=TrialPolicy(repetitions=repetitions),
        reproducibility_policy=ReproducibilityPolicy(),
        metadata=metadata or {"program": "PrimeAIExplorer"},
    )


def campaign(experiments=None):
    return CampaignSpec(
        campaign_id="CAMPAIGN-001",
        title="Cross-provider prime benchmark",
        experiments=tuple(experiments or (experiment(),)),
        execution_policy=ExecutionPolicy(max_parallel_jobs=2),
        metadata={"purpose": "scientific benchmark"},
    )


def test_dataset_spec_rejects_blank_id():
    with pytest.raises(ValidationError):
        DatasetSpec("", "1")


def test_dataset_spec_copies_selector():
    selector = {"window": 64}
    spec = DatasetSpec("d", "1", selector=selector)
    selector["window"] = 4
    assert spec.selector["window"] == 64


def test_prompt_spec_rejects_non_mapping_variables():
    with pytest.raises(ValidationError):
        PromptSpec("p", "1", template_variables=[])


def test_prompt_spec_accepts_optional_system_prompt():
    assert PromptSpec("p", "1").system_prompt_id is None


def test_provider_target_id():
    assert target().target_id == "openai/gpt-test"


def test_provider_target_rejects_negative_temperature():
    with pytest.raises(ValidationError):
        target(temperature=-0.1)


def test_provider_target_rejects_zero_max_tokens():
    with pytest.raises(ValidationError):
        target(max_output_tokens=0)


def test_trial_policy_defaults():
    policy = TrialPolicy()
    assert policy.repetitions == 1
    assert policy.failure_policy == FailurePolicy.CONTINUE


def test_trial_policy_rejects_zero_repetitions():
    with pytest.raises(ValidationError):
        TrialPolicy(repetitions=0)


def test_trial_policy_rejects_negative_retries():
    with pytest.raises(ValidationError):
        TrialPolicy(retries_per_trial=-1)


def test_trial_policy_rejects_nonpositive_timeout():
    with pytest.raises(ValidationError):
        TrialPolicy(timeout_seconds=0)


def test_reproducibility_fixed_requires_seed():
    with pytest.raises(ValidationError):
        ReproducibilityPolicy(seed_policy=SeedPolicy.FIXED, base_seed=None)


def test_execution_policy_rejects_zero_parallelism():
    with pytest.raises(ValidationError):
        ExecutionPolicy(max_parallel_jobs=0)


def test_execution_policy_rejects_failure_tolerance_over_one():
    with pytest.raises(ValidationError):
        ExecutionPolicy(provider_failure_tolerance=1.01)


def test_experiment_requires_targets():
    with pytest.raises(ValidationError):
        experiment(targets=())


def test_experiment_rejects_duplicate_targets():
    with pytest.raises(ValidationError):
        experiment(targets=(target("openai", "m"), target("openai", "m")))


def test_experiment_sorts_targets_deterministically():
    exp = experiment(targets=(target("openai", "z"), target("deepseek", "a")))
    assert [item.target_id for item in exp.provider_targets] == [
        "deepseek/a",
        "openai/z",
    ]


def test_experiment_identity_is_stable():
    assert experiment().experiment_sha256 == experiment().experiment_sha256


def test_experiment_identity_is_64_hex():
    value = experiment().experiment_sha256
    assert len(value) == 64
    int(value, 16)


def test_experiment_identity_ignores_target_input_order():
    a = experiment(targets=(target("openai", "gpt"), target("deepseek", "ds")))
    b = experiment(targets=(target("deepseek", "ds"), target("openai", "gpt")))
    assert a.experiment_sha256 == b.experiment_sha256


def test_experiment_identity_changes_with_trial_policy():
    assert experiment(repetitions=3).experiment_sha256 != experiment(
        repetitions=4
    ).experiment_sha256


def test_experiment_identity_changes_with_metadata():
    assert experiment(metadata={"a": 1}).experiment_sha256 != experiment(
        metadata={"a": 2}
    ).experiment_sha256


def test_experiment_dict_contains_identity():
    data = experiment().to_dict()
    assert data["schema_version"] == "h1.0"
    assert data["experiment_sha256"]


def test_campaign_rejects_empty_experiments():
    with pytest.raises(ValidationError):
        CampaignSpec("C", "Title", ())


def test_campaign_rejects_duplicate_experiment_ids():
    with pytest.raises(ValidationError):
        campaign((experiment("E"), experiment("E")))


def test_campaign_sorts_experiments():
    value = campaign((experiment("EXP-B"), experiment("EXP-A")))
    assert [item.experiment_id for item in value.experiments] == ["EXP-A", "EXP-B"]


def test_campaign_identity_is_order_invariant():
    a = campaign((experiment("EXP-B"), experiment("EXP-A")))
    b = campaign((experiment("EXP-A"), experiment("EXP-B")))
    assert a.campaign_sha256 == b.campaign_sha256


def test_campaign_provider_targets_are_unique_and_sorted():
    value = campaign(
        (
            experiment(
                "A",
                targets=(target("openai", "gpt"), target("deepseek", "ds")),
            ),
            experiment("B", targets=(target("openai", "gpt"),)),
        )
    )
    assert value.provider_targets == ("deepseek/ds", "openai/gpt")


def test_campaign_total_planned_trials():
    value = campaign(
        (
            experiment("A", repetitions=3),
            experiment("B", targets=(target("openai", "gpt"),), repetitions=2),
        )
    )
    assert value.total_planned_trials == 8


def test_campaign_to_dict_contains_summary():
    data = campaign().to_dict()
    assert data["campaign_sha256"]
    assert data["total_planned_trials"] == 6
    assert data["provider_targets"] == [
        "deepseek/deepseek-test",
        "openai/gpt-test",
    ]


def test_experiment_manifest_from_experiment():
    exp = experiment()
    manifest = ExperimentManifest.from_experiment(exp, source="test")
    assert manifest.experiment_id == exp.experiment_id
    assert manifest.experiment_sha256 == exp.experiment_sha256


def test_experiment_manifest_hash_is_stable():
    exp = experiment()
    a = ExperimentManifest.from_experiment(exp, source="test")
    b = ExperimentManifest.from_experiment(exp, source="test")
    assert a.manifest_sha256 == b.manifest_sha256


def test_campaign_manifest_from_campaign():
    value = campaign((experiment("B"), experiment("A")))
    manifest = CampaignManifest.from_campaign(value, source="test")
    assert manifest.campaign_sha256 == value.campaign_sha256
    assert [item.experiment_id for item in manifest.experiment_manifests] == ["A", "B"]


def test_campaign_manifest_hash_is_stable():
    value = campaign()
    a = CampaignManifest.from_campaign(value, source="test")
    b = CampaignManifest.from_campaign(value, source="test")
    assert a.manifest_sha256 == b.manifest_sha256


def test_canonical_json_is_key_order_invariant():
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_contracts_are_json_serializable():
    payload = campaign().to_dict()
    round_trip = json.loads(json.dumps(payload))
    assert round_trip["schema_version"] == "h1.0"


def test_manifest_rejects_non_hex_sha():
    with pytest.raises(ValidationError):
        ExperimentManifest(
            experiment_id="E",
            experiment_sha256="z" * 64,
            source="test",
        )


def test_campaign_identity_changes_when_experiment_changes():
    a = campaign((experiment("E", repetitions=2),))
    b = campaign((experiment("E", repetitions=3),))
    assert a.campaign_sha256 != b.campaign_sha256
