import pytest

from experimental_campaign import (
    DatasetDescriptor,
    DatasetRegistry,
    ExperimentDefinition,
    ExperimentMaterialization,
    ExperimentMaterializer,
    MaterializationManifest,
    PromptRegistry,
    PromptSpec,
    PromptSuite,
    PromptTemplate,
    ProviderTarget,
    ReproducibilityPolicy,
    ResolvedInputSuite,
    SeedPolicy,
    SourceRecord,
    TrialPolicy,
    DatasetSpec,
    ExperimentalInputRegistry,
)
from kernel.exceptions import ValidationError


def build_inputs(*, prompt_version="1", split="default"):
    dataset = DatasetDescriptor(
        dataset_id="prime-gaps",
        version="1",
        uri="repository://prime-gaps/v1",
        format="jsonl",
        split=split,
        record_count=100,
    )
    prompt = PromptTemplate(
        prompt_id="prime-gap-json",
        version=prompt_version,
        template="Observed gaps: {gaps}. Predict the next gap.",
        system_prompt="Return JSON only.",
        json_mode=True,
    )
    registry = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset,)),
        prompts=PromptRegistry(
            prompts=(prompt,),
            suites=(PromptSuite("prime-gap-suite", "1", (f"prime-gap-json@{prompt_version}",)),),
        ),
    )
    return registry.resolve(
        dataset_id="prime-gaps",
        dataset_version="1",
        dataset_split=split,
        prompt_suite_id="prime-gap-suite",
        prompt_suite_version="1",
    )


def build_experiment(
    *,
    repetitions=2,
    seed_policy=SeedPolicy.DERIVED,
    base_seed=17,
    targets=None,
    prompt_version="1",
    split="default",
):
    return ExperimentDefinition(
        experiment_id="EXP-H3-001",
        title="Prime gap materialization",
        task_family="prime-gap-next-value",
        dataset_spec=DatasetSpec(
            dataset_id="prime-gaps",
            version="1",
            split=split,
        ),
        prompt_spec=PromptSpec(
            prompt_id="prime-gap-json",
            version=prompt_version,
        ),
        evaluation_contract_id="prime-gap.numeric-exact",
        provider_targets=tuple(
            targets
            if targets is not None
            else (
                ProviderTarget("openai", "gpt-test"),
                ProviderTarget("deepseek", "deepseek-test"),
            )
        ),
        trial_policy=TrialPolicy(repetitions=repetitions),
        reproducibility_policy=ReproducibilityPolicy(
            seed_policy=seed_policy,
            base_seed=base_seed,
        ),
    )


def records():
    return (
        SourceRecord("R2", {"gaps": "6 4 2 10"}),
        SourceRecord("R1", {"gaps": "2 4 2 6"}),
    )


def materialize(**kwargs):
    experiment = build_experiment(**kwargs)
    return ExperimentMaterializer().materialize(
        experiment=experiment,
        inputs=build_inputs(),
        records=records(),
    )


def test_source_record_requires_id():
    with pytest.raises(ValidationError):
        SourceRecord("", {"x": 1})


def test_source_record_requires_mapping_payload():
    with pytest.raises(ValidationError):
        SourceRecord("R1", [])


def test_source_record_identity_stable():
    assert SourceRecord("R1", {"x": 1}).record_sha256 == SourceRecord(
        "R1", {"x": 1}
    ).record_sha256


def test_materializer_requires_experiment():
    with pytest.raises(ValidationError):
        ExperimentMaterializer().materialize(
            experiment=None,
            inputs=build_inputs(),
            records=records(),
        )


def test_materializer_requires_resolved_inputs():
    with pytest.raises(ValidationError):
        ExperimentMaterializer().materialize(
            experiment=build_experiment(),
            inputs=None,
            records=records(),
        )


def test_dataset_contract_mismatch_rejected():
    with pytest.raises(ValidationError):
        ExperimentMaterializer().materialize(
            experiment=build_experiment(split="other"),
            inputs=build_inputs(split="default"),
            records=records(),
        )


def test_prompt_contract_mismatch_rejected():
    with pytest.raises(ValidationError):
        ExperimentMaterializer().materialize(
            experiment=build_experiment(prompt_version="2"),
            inputs=build_inputs(prompt_version="1"),
            records=records(),
        )


def test_duplicate_record_ids_rejected():
    with pytest.raises(ValidationError):
        ExperimentMaterializer().materialize(
            experiment=build_experiment(),
            inputs=build_inputs(),
            records=(
                SourceRecord("R1", {"gaps": "2 4"}),
                SourceRecord("R1", {"gaps": "6 8"}),
            ),
        )


def test_mapping_records_supported():
    result = ExperimentMaterializer().materialize(
        experiment=build_experiment(repetitions=1),
        inputs=build_inputs(),
        records=(
            {"record_id": "R1", "gaps": "2 4 2 6"},
        ),
    )
    assert result.case_count == 2


def test_explicit_payload_mapping_supported():
    result = ExperimentMaterializer().materialize(
        experiment=build_experiment(repetitions=1),
        inputs=build_inputs(),
        records=(
            {
                "record_id": "R1",
                "payload": {"gaps": "2 4 2 6"},
                "metadata": {"source": "fixture"},
            },
        ),
    )
    assert result.case_count == 2


def test_explicit_payload_mapping_rejects_extra_fields():
    with pytest.raises(ValidationError):
        ExperimentMaterializer().materialize(
            experiment=build_experiment(),
            inputs=build_inputs(),
            records=(
                {
                    "record_id": "R1",
                    "payload": {"gaps": "2 4"},
                    "extra": 1,
                },
            ),
        )


def test_case_count_records_targets_repetitions():
    result = materialize(repetitions=3)
    assert result.case_count == 12


def test_case_order_deterministic():
    result = materialize()
    assert [case.case_id for case in result.cases] == sorted(
        case.case_id for case in result.cases
    )


def test_case_ids_unique():
    result = materialize()
    assert len({case.case_id for case in result.cases}) == result.case_count


def test_case_identity_stable():
    assert materialize().materialization_sha256 == materialize().materialization_sha256


def test_record_input_order_does_not_change_materialization():
    experiment = build_experiment()
    inputs = build_inputs()
    engine = ExperimentMaterializer()
    a = engine.materialize(
        experiment=experiment,
        inputs=inputs,
        records=records(),
    )
    b = engine.materialize(
        experiment=experiment,
        inputs=inputs,
        records=tuple(reversed(records())),
    )
    assert a.materialization_sha256 == b.materialization_sha256


def test_prompt_is_rendered_from_record_payload():
    result = materialize(repetitions=1)
    assert any("2 4 2 6" in case.prompt_text for case in result.cases)


def test_system_prompt_preserved():
    assert all(case.system_prompt == "Return JSON only." for case in materialize().cases)


def test_json_mode_preserved():
    assert all(case.json_mode is True for case in materialize().cases)


def test_provider_target_preserved():
    targets = {case.target_id for case in materialize().cases}
    assert targets == {"deepseek/deepseek-test", "openai/gpt-test"}


def test_repetition_indices_present():
    values = {case.repetition_index for case in materialize(repetitions=3).cases}
    assert values == {1, 2, 3}


def test_none_seed_policy_yields_none():
    result = materialize(seed_policy=SeedPolicy.NONE, base_seed=None)
    assert all(case.seed is None for case in result.cases)


def test_fixed_seed_policy_uses_base_seed():
    result = materialize(seed_policy=SeedPolicy.FIXED, base_seed=123)
    assert {case.seed for case in result.cases} == {123}


def test_explicit_target_seed_overrides_policy():
    result = materialize(
        targets=(ProviderTarget("openai", "gpt-test", seed=999),),
        seed_policy=SeedPolicy.DERIVED,
    )
    assert {case.seed for case in result.cases} == {999}


def test_derived_seed_is_deterministic():
    a = materialize(seed_policy=SeedPolicy.DERIVED)
    b = materialize(seed_policy=SeedPolicy.DERIVED)
    assert [case.seed for case in a.cases] == [case.seed for case in b.cases]


def test_derived_seed_varies_across_trials():
    result = materialize(
        targets=(ProviderTarget("openai", "gpt-test"),),
        repetitions=3,
    )
    seeds = [case.seed for case in result.cases if case.source_record_id == "R1"]
    assert len(set(seeds)) == 3


def test_case_contains_experiment_provenance():
    experiment = build_experiment()
    result = ExperimentMaterializer().materialize(
        experiment=experiment,
        inputs=build_inputs(),
        records=records(),
    )
    assert all(
        case.experiment_sha256 == experiment.experiment_sha256
        for case in result.cases
    )


def test_case_contains_dataset_provenance():
    inputs = build_inputs()
    result = ExperimentMaterializer().materialize(
        experiment=build_experiment(),
        inputs=inputs,
        records=records(),
    )
    assert all(
        case.dataset_descriptor_sha256 == inputs.dataset.descriptor_sha256
        for case in result.cases
    )


def test_case_contains_prompt_provenance():
    inputs = build_inputs()
    prompt = inputs.prompts[0]
    result = ExperimentMaterializer().materialize(
        experiment=build_experiment(),
        inputs=inputs,
        records=records(),
    )
    assert all(case.prompt_sha256 == prompt.prompt_sha256 for case in result.cases)


def test_materialization_to_dict_has_cases():
    payload = materialize().to_dict()
    assert payload["schema_version"] == "h3.0"
    assert payload["case_count"] == len(payload["cases"])


def test_empty_records_are_valid_zero_case_materialization():
    result = ExperimentMaterializer().materialize(
        experiment=build_experiment(),
        inputs=build_inputs(),
        records=(),
    )
    assert result.case_count == 0


def test_materialization_manifest_from_materialization():
    result = materialize()
    manifest = MaterializationManifest.from_materialization(
        result,
        source="unit-test",
    )
    assert manifest.case_count == result.case_count
    assert manifest.materialization_sha256 == result.materialization_sha256


def test_materialization_manifest_identity_stable():
    result = materialize()
    a = MaterializationManifest.from_materialization(result, source="unit-test")
    b = MaterializationManifest.from_materialization(result, source="unit-test")
    assert a.manifest_sha256 == b.manifest_sha256


def test_materialization_manifest_rejects_bad_case_count():
    with pytest.raises(ValidationError):
        MaterializationManifest(
            experiment_id="E",
            experiment_sha256="a" * 64,
            input_suite_sha256="b" * 64,
            materialization_sha256="c" * 64,
            case_count=2,
            case_ids=("C1",),
            source="test",
        )


def test_experiment_materialization_rejects_duplicate_case_ids():
    base = materialize(repetitions=1)
    case = base.cases[0]
    with pytest.raises(ValidationError):
        ExperimentMaterialization(
            experiment_id=base.experiment_id,
            experiment_sha256=base.experiment_sha256,
            input_suite_sha256=base.input_suite_sha256,
            cases=(case, case),
        )


def test_materialization_changes_when_record_changes():
    experiment = build_experiment()
    inputs = build_inputs()
    engine = ExperimentMaterializer()
    a = engine.materialize(
        experiment=experiment,
        inputs=inputs,
        records=(SourceRecord("R1", {"gaps": "2 4"}),),
    )
    b = engine.materialize(
        experiment=experiment,
        inputs=inputs,
        records=(SourceRecord("R1", {"gaps": "2 6"}),),
    )
    assert a.materialization_sha256 != b.materialization_sha256


def test_materialization_changes_when_repetitions_change():
    assert materialize(repetitions=1).materialization_sha256 != materialize(
        repetitions=2
    ).materialization_sha256
