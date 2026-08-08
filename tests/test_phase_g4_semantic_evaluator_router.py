import pytest

from behavioral_evaluation import (
    BehavioralEvaluationContract,
    BehavioralProviderExecutionBridge,
    BehavioralRequestSpec,
    ObservationLedger,
    TrialPlan,
)
from behavioral_evaluation.evaluator_registry import (
    SemanticEvaluatorRegistry,
    default_semantic_evaluator_registry,
)
from behavioral_evaluation.evaluators import (
    ExactIntegerEvaluator,
    ExactTextEvaluator,
    SemanticEvaluationRequest,
    StructuredPredictionEvaluator,
    extract_confidence,
    parse_first_integer,
    parse_json_object,
)
from behavioral_evaluation.routing import SemanticEvaluatorRouter
from behavioral_evaluation.execution import EvaluationOutcome
from kernel.exceptions import ValidationError
from model_providers import ProviderCapabilities, ProviderResponse, ProviderUsage


def response(text, **overrides):
    values = dict(
        provider="openai",
        model="gpt-test",
        text=text,
        latency_seconds=0.25,
        usage=ProviderUsage(
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
        ),
    )
    values.update(overrides)
    return ProviderResponse(**values)


def numeric_contract():
    return BehavioralEvaluationContract(
        contract_id="prime-gap.numeric-exact",
        evaluator_id="numeric_exact",
    )


def structured_contract():
    return BehavioralEvaluationContract(
        contract_id="prediction.structured",
        evaluator_id="structured_prediction",
    )


def test_parse_json_object_direct_json():
    assert parse_json_object('{"prediction":4}') == {"prediction": 4}


def test_parse_json_object_embedded_json():
    assert parse_json_object('answer: {"prediction":4} done') == {"prediction": 4}


def test_parse_json_object_invalid_returns_none():
    assert parse_json_object("not json") is None


def test_parse_first_integer_from_prediction_json():
    assert parse_first_integer('{"prediction":4}') == 4


def test_parse_first_integer_from_text():
    assert parse_first_integer("The answer is 6.") == 6


def test_confidence_extraction():
    assert extract_confidence('{"prediction":4,"confidence":83}') == 83


def test_invalid_confidence_is_ignored():
    assert extract_confidence('{"prediction":4,"confidence":120}') is None


def test_exact_integer_pass():
    outcome = ExactIntegerEvaluator().evaluate(
        response('{"prediction":4,"confidence":80}'),
        SemanticEvaluationRequest(expected=4),
    )
    assert outcome.passed is True
    assert outcome.score == 100.0
    assert outcome.semantic_answer == 4
    assert outcome.confidence == 80


def test_exact_integer_fail():
    outcome = ExactIntegerEvaluator().evaluate(
        response('{"prediction":6}'),
        SemanticEvaluationRequest(expected=4),
    )
    assert outcome.passed is False
    assert outcome.score == 0.0


def test_exact_integer_rejects_non_integer_expected():
    with pytest.raises(ValidationError):
        ExactIntegerEvaluator().evaluate(
            response("4"),
            SemanticEvaluationRequest(expected="4"),
        )


def test_exact_text_pass():
    outcome = ExactTextEvaluator().evaluate(
        response("alpha"),
        SemanticEvaluationRequest(expected="alpha"),
    )
    assert outcome.passed is True


def test_exact_text_fail():
    outcome = ExactTextEvaluator().evaluate(
        response("beta"),
        SemanticEvaluationRequest(expected="alpha"),
    )
    assert outcome.passed is False


def test_structured_prediction_all_fields_pass():
    outcome = StructuredPredictionEvaluator().evaluate(
        response('{"prediction":4,"label":"stable","confidence":90}'),
        SemanticEvaluationRequest(
            expected={"prediction": 4, "label": "stable"}
        ),
    )
    assert outcome.passed is True
    assert outcome.score == 100.0
    assert outcome.confidence == 90


def test_structured_prediction_allows_extra_fields():
    outcome = StructuredPredictionEvaluator().evaluate(
        response('{"prediction":4,"extra":"ok"}'),
        SemanticEvaluationRequest(expected={"prediction": 4}),
    )
    assert outcome.passed is True


def test_structured_prediction_partial_score():
    outcome = StructuredPredictionEvaluator().evaluate(
        response('{"prediction":4,"label":"wrong"}'),
        SemanticEvaluationRequest(
            expected={"prediction": 4, "label": "stable"}
        ),
    )
    assert outcome.passed is False
    assert outcome.score == 50.0


def test_structured_prediction_invalid_json_fails_cleanly():
    outcome = StructuredPredictionEvaluator().evaluate(
        response("not-json"),
        SemanticEvaluationRequest(expected={"prediction": 4}),
    )
    assert outcome.passed is False
    assert outcome.score == 0.0
    assert outcome.semantic_answer is None


def test_structured_prediction_requires_mapping_expected():
    with pytest.raises(ValidationError):
        StructuredPredictionEvaluator().evaluate(
            response('{"prediction":4}'),
            SemanticEvaluationRequest(expected=4),
        )


def test_registry_default_names_are_deterministic():
    registry = default_semantic_evaluator_registry()
    assert registry.names() == (
        "numeric_exact",
        "structured_prediction",
        "text_exact",
    )


def test_registry_rejects_duplicate():
    registry = SemanticEvaluatorRegistry((ExactIntegerEvaluator(),))
    with pytest.raises(ValidationError):
        registry.register(ExactIntegerEvaluator())


def test_registry_unknown_evaluator():
    with pytest.raises(KeyError):
        default_semantic_evaluator_registry().get("missing")


def test_router_uses_contract_evaluator_id():
    router = SemanticEvaluatorRouter()
    outcome = router.evaluate(
        contract=numeric_contract(),
        response=response('{"prediction":4}'),
        expected=4,
    )
    assert outcome.passed is True
    assert outcome.metadata["contract_id"] == "prime-gap.numeric-exact"


def test_router_preserves_contract_hash():
    contract = numeric_contract()
    outcome = SemanticEvaluatorRouter().evaluate(
        contract=contract,
        response=response("4"),
        expected=4,
    )
    assert outcome.metadata["contract_sha256"] == contract.contract_sha256


def test_router_unknown_evaluator_fails():
    contract = BehavioralEvaluationContract(
        contract_id="x",
        evaluator_id="does-not-exist",
    )
    with pytest.raises(KeyError):
        SemanticEvaluatorRouter().evaluate(
            contract=contract,
            response=response("x"),
            expected="x",
        )


def test_outcome_builder_is_g3_compatible():
    builder = SemanticEvaluatorRouter().outcome_builder(
        contract=numeric_contract(),
        expected=4,
    )
    outcome = builder(response('{"prediction":4}'))
    assert isinstance(outcome, EvaluationOutcome)
    assert outcome.passed is True


class FakeProvider:
    name = "openai"
    capabilities = ProviderCapabilities()

    def __init__(self, provider_response):
        self.provider_response = provider_response

    def generate(self, request):
        return self.provider_response


def test_router_integrates_with_g3_bridge():
    contract = numeric_contract()
    plan = TrialPlan.from_contract(
        run_id="RUN-G4-001",
        providers=(("openai", "gpt-test"),),
        case_ids=("CASE-001",),
        trials_per_case=1,
        contract=contract,
    )
    trial = plan.iter_trials()[0]
    ledger = ObservationLedger(plan, ())

    provider = FakeProvider(
        response('{"prediction":4,"confidence":77}')
    )
    router = SemanticEvaluatorRouter()
    bridge = BehavioralProviderExecutionBridge(
        provider,
        router.outcome_builder(
            contract=contract,
            expected=4,
        ),
    )

    updated = bridge.execute_into(
        ledger,
        trial,
        BehavioralRequestSpec(
            prompt="Predict the next prime gap.",
            json_mode=True,
        ),
    )

    record = updated.records[0]
    assert updated.complete is True
    assert record.passed is True
    assert record.score == 100.0
    assert record.confidence == 77
    assert record.semantic_answer == 4
    assert record.metadata["evaluation_metadata"]["contract_id"] == contract.contract_id


def test_router_integration_records_semantic_failure_not_provider_error():
    contract = numeric_contract()
    plan = TrialPlan.from_contract(
        run_id="RUN-G4-002",
        providers=(("openai", "gpt-test"),),
        case_ids=("CASE-001",),
        trials_per_case=1,
        contract=contract,
    )
    trial = plan.iter_trials()[0]

    provider = FakeProvider(response('{"prediction":6}'))
    bridge = BehavioralProviderExecutionBridge(
        provider,
        SemanticEvaluatorRouter().outcome_builder(
            contract=contract,
            expected=4,
        ),
    )

    record = bridge.execute(
        trial,
        BehavioralRequestSpec(prompt="Predict."),
    )

    assert record.execution_status.value == "completed"
    assert record.evaluation_disposition.value == "evaluated"
    assert record.passed is False
    assert record.score == 0.0
    assert record.provider_error_category is None


def test_semantic_request_metadata_is_mapping():
    with pytest.raises(ValidationError):
        SemanticEvaluationRequest(expected=4, metadata="bad")


def test_router_metadata_is_mapping():
    with pytest.raises(ValidationError):
        SemanticEvaluatorRouter().evaluate(
            contract=numeric_contract(),
            response=response("4"),
            expected=4,
            metadata="bad",
        )
