import pytest

from behavioral_evaluation import (
    BehavioralEvaluationContract,
    BehavioralEvaluationContractRegistry,
    BehavioralEvaluationRecord,
    EvaluationDisposition,
    ProviderExecutionStatus,
)
from kernel.exceptions import ValidationError


def contract():
    return BehavioralEvaluationContract(
        contract_id="prime-gap.numeric-exact",
        evaluator_id="numeric_exact",
        canonicalizer_id="numeric",
        requires_confidence=True,
    )


def evaluated_record(**overrides):
    values = dict(
        observation_id="OBS-0001",
        contract_id="prime-gap.numeric-exact",
        case_id="CASE-0001",
        trial_index=1,
        provider="openai",
        model="example-model",
        execution_status=ProviderExecutionStatus.COMPLETED,
        evaluation_disposition=EvaluationDisposition.EVALUATED,
        response_sha256="a" * 64,
        passed=True,
        score=100.0,
        confidence=80,
        latency_seconds=1.25,
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        surface_answer="4",
        semantic_answer=4,
    )
    values.update(overrides)
    return BehavioralEvaluationRecord(**values)


def provider_error_record(**overrides):
    values = dict(
        observation_id="OBS-ERR-0001",
        contract_id="prime-gap.numeric-exact",
        case_id="CASE-0001",
        trial_index=1,
        provider="deepseek",
        model="example-model",
        execution_status=ProviderExecutionStatus.PROVIDER_ERROR,
        evaluation_disposition=EvaluationDisposition.NOT_EVALUATED,
        provider_error_category="billing",
        provider_error_message="Insufficient Balance",
    )
    values.update(overrides)
    return BehavioralEvaluationRecord(**values)


def test_contract_round_trip_hash():
    rebuilt = BehavioralEvaluationContract.from_mapping(contract().to_dict())
    assert rebuilt.contract_sha256 == contract().contract_sha256


def test_contract_rejects_empty_identity():
    with pytest.raises(ValidationError):
        BehavioralEvaluationContract("", "numeric_exact")


def test_contract_rejects_invalid_score_range():
    with pytest.raises(ValidationError):
        BehavioralEvaluationContract("x", "exact", score_min=100, score_max=100)


def test_registry_is_deterministic():
    registry = BehavioralEvaluationContractRegistry([
        BehavioralEvaluationContract("z", "exact"),
        BehavioralEvaluationContract("a", "exact"),
    ])
    assert registry.names() == ("a", "z")


def test_registry_rejects_duplicates():
    registry = BehavioralEvaluationContractRegistry([contract()])
    with pytest.raises(ValidationError):
        registry.register(contract())


def test_registry_get():
    registry = BehavioralEvaluationContractRegistry([contract()])
    assert registry.get(contract().contract_id) == contract()


def test_evaluated_record_is_scored():
    r = evaluated_record()
    assert r.passed is True
    assert r.score == 100.0


def test_provider_error_is_not_scored():
    r = provider_error_record()
    assert r.passed is None
    assert r.score is None


def test_provider_error_cannot_carry_zero_score():
    with pytest.raises(ValidationError):
        provider_error_record(passed=False, score=0.0)


def test_provider_error_requires_not_evaluated():
    with pytest.raises(ValidationError):
        provider_error_record(
            evaluation_disposition=EvaluationDisposition.EVALUATED
        )


def test_completed_requires_evaluated():
    with pytest.raises(ValidationError):
        evaluated_record(
            evaluation_disposition=EvaluationDisposition.NOT_EVALUATED
        )


def test_completed_requires_passed():
    with pytest.raises(ValidationError):
        evaluated_record(passed=None)


def test_score_range_is_enforced():
    with pytest.raises(ValidationError):
        evaluated_record(score=101.0)


def test_record_hash_is_stable_for_metadata_order():
    a = evaluated_record(metadata={"b": 2, "a": 1})
    b = evaluated_record(metadata={"a": 1, "b": 2})
    assert a.record_sha256 == b.record_sha256
