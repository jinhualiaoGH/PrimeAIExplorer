import pytest

from experimental_campaign import (
    DatasetDescriptor,
    DatasetRegistry,
    ExperimentalInputRegistry,
    PromptRegistry,
    PromptSuite,
    PromptTemplate,
    ResolvedInputSuite,
)
from kernel.exceptions import ValidationError


def dataset(**kwargs):
    values = {
        "dataset_id": "prime-gaps",
        "version": "1",
        "uri": "repository://prime-gaps/v1",
        "format": "jsonl",
        "split": "default",
        "record_count": 1000,
    }
    values.update(kwargs)
    return DatasetDescriptor(**values)


def prompt(prompt_id="prime-gap-json", version="1", template="Predict {value}.", **kwargs):
    return PromptTemplate(
        prompt_id=prompt_id,
        version=version,
        template=template,
        **kwargs,
    )


def suite(refs=None):
    return PromptSuite(
        suite_id="prime-gap-suite",
        version="1",
        prompt_refs=tuple(refs or ("prime-gap-json@1",)),
    )


def test_dataset_descriptor_registry_id():
    assert dataset().registry_id == "prime-gaps@1#default"


def test_dataset_descriptor_identity_stable():
    assert dataset().descriptor_sha256 == dataset().descriptor_sha256


def test_dataset_descriptor_identity_is_hex():
    value = dataset().descriptor_sha256
    assert len(value) == 64
    int(value, 16)


def test_dataset_descriptor_rejects_negative_record_count():
    with pytest.raises(ValidationError):
        dataset(record_count=-1)


def test_dataset_descriptor_accepts_zero_record_count():
    assert dataset(record_count=0).record_count == 0


def test_dataset_descriptor_rejects_bad_content_hash():
    with pytest.raises(ValidationError):
        dataset(content_sha256="x" * 64)


def test_dataset_descriptor_normalizes_content_hash_case():
    value = "A" * 64
    assert dataset(content_sha256=value).content_sha256 == value.lower()


def test_dataset_to_h1_dataset_spec():
    spec = dataset().to_dataset_spec(selector={"window": 64})
    assert spec.dataset_id == "prime-gaps"
    assert spec.version == "1"
    assert spec.selector == {"window": 64}
    assert spec.metadata["descriptor_sha256"]


def test_dataset_registry_register_and_get():
    registry = DatasetRegistry()
    item = registry.register(dataset())
    assert registry.get("prime-gaps", "1") == item


def test_dataset_registry_duplicate_identical_is_idempotent():
    registry = DatasetRegistry()
    first = registry.register(dataset())
    second = registry.register(dataset())
    assert first == second


def test_dataset_registry_conflict_rejected():
    registry = DatasetRegistry((dataset(),))
    with pytest.raises(ValidationError):
        registry.register(dataset(uri="repository://different"))


def test_dataset_registry_missing_raises_keyerror():
    with pytest.raises(KeyError):
        DatasetRegistry().get("missing", "1")


def test_dataset_registry_order_is_deterministic():
    registry = DatasetRegistry(
        (
            dataset(dataset_id="z"),
            dataset(dataset_id="a"),
        )
    )
    assert [item.dataset_id for item in registry.items()] == ["a", "z"]


def test_prompt_registry_id():
    assert prompt().registry_id == "prime-gap-json@1"


def test_prompt_identity_stable():
    assert prompt().prompt_sha256 == prompt().prompt_sha256


def test_prompt_render():
    assert prompt().render({"value": 42}) == "Predict 42."


def test_prompt_render_missing_variable_rejected():
    with pytest.raises(ValidationError):
        prompt().render({})


def test_prompt_to_h1_prompt_spec():
    spec = prompt().to_prompt_spec(template_variables={"value": 4})
    assert spec.prompt_id == "prime-gap-json"
    assert spec.version == "1"
    assert spec.template_variables == {"value": 4}
    assert spec.metadata["prompt_sha256"]


def test_prompt_rejects_blank_template():
    with pytest.raises(ValidationError):
        prompt(template="")


def test_prompt_suite_requires_refs():
    with pytest.raises(ValidationError):
        PromptSuite("s", "1", ())


def test_prompt_suite_rejects_duplicate_refs():
    with pytest.raises(ValidationError):
        PromptSuite("s", "1", ("p@1", "p@1"))


def test_prompt_suite_normalizes_reference_order():
    value = PromptSuite("s", "1", ("z@1", "a@1"))
    assert value.prompt_refs == ("a@1", "z@1")


def test_prompt_suite_identity_order_invariant():
    a = PromptSuite("s", "1", ("z@1", "a@1"))
    b = PromptSuite("s", "1", ("a@1", "z@1"))
    assert a.suite_sha256 == b.suite_sha256


def test_prompt_registry_register_prompt_and_get():
    registry = PromptRegistry()
    item = registry.register_prompt(prompt())
    assert registry.get_prompt("prime-gap-json", "1") == item


def test_prompt_registry_prompt_conflict_rejected():
    registry = PromptRegistry((prompt(),))
    with pytest.raises(ValidationError):
        registry.register_prompt(prompt(template="Changed {value}"))


def test_prompt_registry_register_suite_and_get():
    registry = PromptRegistry(prompts=(prompt(),))
    item = registry.register_suite(suite())
    assert registry.get_suite("prime-gap-suite", "1") == item


def test_prompt_registry_suite_conflict_rejected():
    registry = PromptRegistry(
        prompts=(prompt(), prompt("other")),
        suites=(suite(),),
    )
    with pytest.raises(ValidationError):
        registry.register_suite(
            PromptSuite("prime-gap-suite", "1", ("other@1",))
        )


def test_prompt_registry_order_is_deterministic():
    registry = PromptRegistry(
        prompts=(
            prompt("z"),
            prompt("a"),
        )
    )
    assert [item.prompt_id for item in registry.prompt_items()] == ["a", "z"]


def test_input_registry_resolution():
    registry = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset(),)),
        prompts=PromptRegistry(
            prompts=(prompt(),),
            suites=(suite(),),
        ),
    )
    result = registry.resolve(
        dataset_id="prime-gaps",
        dataset_version="1",
        prompt_suite_id="prime-gap-suite",
        prompt_suite_version="1",
        dataset_selector={"window": 64},
    )
    assert isinstance(result, ResolvedInputSuite)
    assert result.dataset_spec.selector == {"window": 64}
    assert len(result.prompt_specs) == 1


def test_input_registry_resolution_rejects_bad_prompt_ref():
    registry = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset(),)),
        prompts=PromptRegistry(
            prompts=(prompt(),),
            suites=(PromptSuite("bad", "1", ("bad-reference",)),),
        ),
    )
    with pytest.raises(ValidationError):
        registry.resolve(
            dataset_id="prime-gaps",
            dataset_version="1",
            prompt_suite_id="bad",
            prompt_suite_version="1",
        )


def test_input_registry_resolution_missing_prompt_raises():
    registry = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset(),)),
        prompts=PromptRegistry(
            suites=(PromptSuite("s", "1", ("missing@1",)),),
        ),
    )
    with pytest.raises(KeyError):
        registry.resolve(
            dataset_id="prime-gaps",
            dataset_version="1",
            prompt_suite_id="s",
            prompt_suite_version="1",
        )


def test_resolved_suite_identity_stable():
    registry = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset(),)),
        prompts=PromptRegistry(
            prompts=(prompt(),),
            suites=(suite(),),
        ),
    )
    a = registry.resolve(
        dataset_id="prime-gaps",
        dataset_version="1",
        prompt_suite_id="prime-gap-suite",
        prompt_suite_version="1",
    )
    b = registry.resolve(
        dataset_id="prime-gaps",
        dataset_version="1",
        prompt_suite_id="prime-gap-suite",
        prompt_suite_version="1",
    )
    assert a.suite_sha256 == b.suite_sha256


def test_registry_identity_stable():
    registry = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset(),)),
        prompts=PromptRegistry(
            prompts=(prompt(),),
            suites=(suite(),),
        ),
    )
    assert registry.registry_sha256 == registry.registry_sha256


def test_registry_identity_changes_with_dataset():
    a = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset(),))
    )
    b = ExperimentalInputRegistry(
        datasets=DatasetRegistry((dataset(uri="repository://changed"),))
    )
    assert a.registry_sha256 != b.registry_sha256


def test_registry_identity_changes_with_prompt():
    a = ExperimentalInputRegistry(
        prompts=PromptRegistry(prompts=(prompt(),))
    )
    b = ExperimentalInputRegistry(
        prompts=PromptRegistry(prompts=(prompt(template="Changed {value}"),))
    )
    assert a.registry_sha256 != b.registry_sha256


def test_registry_to_dict_is_deterministic():
    a = ExperimentalInputRegistry(
        datasets=DatasetRegistry(
            (
                dataset(dataset_id="z"),
                dataset(dataset_id="a"),
            )
        ),
        prompts=PromptRegistry(
            prompts=(
                prompt("z"),
                prompt("a"),
            )
        ),
    )
    b = ExperimentalInputRegistry(
        datasets=DatasetRegistry(
            (
                dataset(dataset_id="a"),
                dataset(dataset_id="z"),
            )
        ),
        prompts=PromptRegistry(
            prompts=(
                prompt("a"),
                prompt("z"),
            )
        ),
    )
    assert a.to_dict() == b.to_dict()
