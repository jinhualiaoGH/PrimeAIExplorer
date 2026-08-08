import pytest

from behavioral_evaluation import (
    BehavioralEvaluationContract,
    EvaluationDisposition,
    ObservationLedger,
    ProviderExecutionStatus,
    TrialPlan,
)
from behavioral_evaluation.execution import (
    BehavioralProviderExecutionBridge,
    BehavioralRequestSpec,
    EvaluationOutcome,
    classify_provider_error,
)
from kernel.exceptions import ValidationError
from model_providers import ProviderCapabilities, ProviderResponse, ProviderUsage


class FakeProvider:
    name = "openai"
    capabilities = ProviderCapabilities()

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


def contract():
    return BehavioralEvaluationContract(
        contract_id="prime-gap.numeric-exact",
        evaluator_id="numeric_exact",
    )


def plan():
    return TrialPlan.from_contract(
        run_id="RUN-G3-001",
        providers=(("openai", "gpt-test"),),
        case_ids=("CASE-001",),
        trials_per_case=2,
        contract=contract(),
    )


def response(**overrides):
    values = dict(
        provider="openai",
        model="gpt-test",
        text='{"prediction":4,"confidence":80}',
        latency_seconds=1.25,
        request_id="req-1",
        finish_reason="stop",
        usage=ProviderUsage(
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
        ),
        metadata={"endpoint": "test"},
    )
    values.update(overrides)
    return ProviderResponse(**values)


def outcome_builder(provider_response):
    return EvaluationOutcome(
        passed=True,
        score=100.0,
        confidence=80,
        surface_answer=provider_response.text,
        semantic_answer=4,
        metadata={"evaluator": "numeric_exact"},
    )


def bridge(fake=None):
    return BehavioralProviderExecutionBridge(
        fake or FakeProvider(response=response()),
        outcome_builder,
    )


def request_spec():
    return BehavioralRequestSpec(
        prompt="Predict the next prime gap.",
        system_prompt="Return JSON only.",
        temperature=0.0,
        max_output_tokens=100,
        seed=7,
        json_mode=True,
        metadata={"campaign": "g3-test"},
    )


def test_request_spec_builds_f2_model_request():
    trial = plan().iter_trials()[0]
    req = request_spec().build_request(trial)
    assert req.model == "gpt-test"
    assert req.prompt == "Predict the next prime gap."
    assert req.metadata["observation_id"] == trial.observation_id
    assert req.metadata["trial_index"] == 1


def test_request_spec_rejects_empty_prompt():
    with pytest.raises(ValidationError):
        BehavioralRequestSpec(prompt="")


def test_successful_provider_execution_becomes_evaluated_record():
    trial = plan().iter_trials()[0]
    record = bridge().execute(trial, request_spec())
    assert record.execution_status is ProviderExecutionStatus.COMPLETED
    assert record.evaluation_disposition is EvaluationDisposition.EVALUATED
    assert record.passed is True
    assert record.score == 100.0


def test_success_preserves_usage_and_latency():
    trial = plan().iter_trials()[0]
    record = bridge().execute(trial, request_spec())
    assert record.latency_seconds == 1.25
    assert record.input_tokens == 10
    assert record.output_tokens == 5
    assert record.total_tokens == 15


def test_success_preserves_request_and_finish_metadata():
    trial = plan().iter_trials()[0]
    record = bridge().execute(trial, request_spec())
    assert record.metadata["provider_request_id"] == "req-1"
    assert record.metadata["finish_reason"] == "stop"
    assert record.metadata["provider_metadata"]["endpoint"] == "test"


def test_success_has_deterministic_response_hash():
    trial = plan().iter_trials()[0]
    a = bridge().execute(trial, request_spec())
    b = bridge().execute(trial, request_spec())
    assert a.response_sha256 == b.response_sha256
    assert len(a.response_sha256) == 64


def test_bridge_invokes_provider_exactly_once():
    fake = FakeProvider(response=response())
    trial = plan().iter_trials()[0]
    bridge(fake).execute(trial, request_spec())
    assert len(fake.requests) == 1


def test_provider_error_becomes_not_evaluated_record():
    fake = FakeProvider(error=RuntimeError("HTTP 402 Insufficient Balance"))
    trial = plan().iter_trials()[0]
    record = bridge(fake).execute(trial, request_spec())
    assert record.execution_status is ProviderExecutionStatus.PROVIDER_ERROR
    assert record.evaluation_disposition is EvaluationDisposition.NOT_EVALUATED
    assert record.passed is None
    assert record.score is None
    assert record.provider_error_category == "billing"


def test_provider_error_does_not_call_outcome_builder():
    calls = []
    def evaluator(_):
        calls.append(True)
        return EvaluationOutcome(True, 100)
    fake = FakeProvider(error=TimeoutError("timed out"))
    b = BehavioralProviderExecutionBridge(fake, evaluator)
    b.execute(plan().iter_trials()[0], request_spec())
    assert calls == []


@pytest.mark.parametrize(
    ("exc", "category"),
    [
        (TimeoutError("timed out"), "timeout"),
        (RuntimeError("HTTP 401 Unauthorized"), "authentication"),
        (RuntimeError("HTTP 429 rate limit"), "rate_limit"),
        (RuntimeError("HTTP 402 Insufficient Balance"), "billing"),
        (ConnectionError("network down"), "network"),
        (RuntimeError("unexpected"), "provider_exception"),
    ],
)
def test_error_classification(exc, category):
    assert classify_provider_error(exc) == category


def test_response_provider_must_match_trial():
    fake = FakeProvider(response=response(provider="anthropic"))
    with pytest.raises(ValidationError):
        bridge(fake).execute(plan().iter_trials()[0], request_spec())


def test_response_model_must_match_trial():
    fake = FakeProvider(response=response(model="wrong-model"))
    with pytest.raises(ValidationError):
        bridge(fake).execute(plan().iter_trials()[0], request_spec())


def test_outcome_builder_must_return_evaluation_outcome():
    fake = FakeProvider(response=response())
    b = BehavioralProviderExecutionBridge(fake, lambda _: {"score": 100})
    with pytest.raises(ValidationError):
        b.execute(plan().iter_trials()[0], request_spec())


def test_execute_into_appends_to_ledger():
    p = plan()
    trial = p.iter_trials()[0]
    ledger = ObservationLedger(p, ())
    updated = bridge().execute_into(ledger, trial, request_spec())
    assert ledger.completed == 0
    assert updated.completed == 1
    assert updated.remaining == 1


def test_execute_into_rejects_already_recorded_trial():
    p = plan()
    trial = p.iter_trials()[0]
    ledger = ObservationLedger(p, ())
    updated = bridge().execute_into(ledger, trial, request_spec())
    with pytest.raises(ValidationError):
        bridge().execute_into(updated, trial, request_spec())


def test_provider_error_counts_as_recorded_observation():
    p = plan()
    trial = p.iter_trials()[0]
    ledger = ObservationLedger(p, ())
    fake = FakeProvider(error=TimeoutError("timed out"))
    updated = bridge(fake).execute_into(ledger, trial, request_spec())
    assert updated.completed == 1
    assert updated.remaining == 1


def test_second_trial_gets_distinct_observation_identity():
    p = plan()
    first, second = p.iter_trials()
    assert first.observation_id != second.observation_id


def test_evaluation_outcome_validates_score():
    with pytest.raises(ValidationError):
        EvaluationOutcome(passed=True, score=101)


def test_evaluation_outcome_validates_confidence():
    with pytest.raises(ValidationError):
        EvaluationOutcome(passed=True, score=100, confidence=101)
