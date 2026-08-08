import pytest

from behavioral_evaluation import (
    BehavioralEvaluationContract,
    BehavioralEvaluationRecord,
    EvaluationDisposition,
    ProviderExecutionStatus,
)
from behavioral_evaluation.manifest import RepeatedTrialRunManifest
from behavioral_evaluation.observations import ObservationLedger, merge_ledgers
from behavioral_evaluation.trials import TrialPlan, TrialSpec
from kernel.exceptions import ValidationError


def contract():
    return BehavioralEvaluationContract(
        contract_id="prime-gap.numeric-exact",
        evaluator_id="numeric_exact",
    )


def plan():
    return TrialPlan.from_contract(
        run_id="RUN-G2-001",
        providers=(("openai", "gpt-example"), ("deepseek", "ds-example")),
        case_ids=("CASE-B", "CASE-A"),
        trials_per_case=2,
        contract=contract(),
    )


def completed_record(trial: TrialSpec, *, score=100.0):
    return BehavioralEvaluationRecord(
        observation_id=trial.observation_id,
        contract_id=trial.contract_id,
        case_id=trial.case_id,
        trial_index=trial.trial_index,
        provider=trial.provider,
        model=trial.model,
        execution_status=ProviderExecutionStatus.COMPLETED,
        evaluation_disposition=EvaluationDisposition.EVALUATED,
        passed=score == 100.0,
        score=score,
    )


def error_record(trial: TrialSpec):
    return BehavioralEvaluationRecord(
        observation_id=trial.observation_id,
        contract_id=trial.contract_id,
        case_id=trial.case_id,
        trial_index=trial.trial_index,
        provider=trial.provider,
        model=trial.model,
        execution_status=ProviderExecutionStatus.PROVIDER_ERROR,
        evaluation_disposition=EvaluationDisposition.NOT_EVALUATED,
        provider_error_category="transient",
    )


def test_trial_identity_is_deterministic():
    a = TrialSpec("RUN", "openai", "m", "CASE", 1, "c")
    b = TrialSpec("RUN", "openai", "m", "CASE", 1, "c")
    assert a.observation_id == b.observation_id


def test_trial_identity_changes_with_trial_index():
    a = TrialSpec("RUN", "openai", "m", "CASE", 1, "c")
    b = TrialSpec("RUN", "openai", "m", "CASE", 2, "c")
    assert a.observation_id != b.observation_id


def test_plan_total_trials():
    assert plan().total_trials == 8


def test_plan_order_is_deterministic():
    trials = plan().iter_trials()
    assert [(x.provider, x.case_id, x.trial_index) for x in trials] == [
        ("deepseek", "CASE-A", 1),
        ("deepseek", "CASE-A", 2),
        ("deepseek", "CASE-B", 1),
        ("deepseek", "CASE-B", 2),
        ("openai", "CASE-A", 1),
        ("openai", "CASE-A", 2),
        ("openai", "CASE-B", 1),
        ("openai", "CASE-B", 2),
    ]


def test_plan_hash_is_input_order_independent():
    a = plan()
    b = TrialPlan.from_contract(
        run_id="RUN-G2-001",
        providers=(("deepseek", "ds-example"), ("openai", "gpt-example")),
        case_ids=("CASE-A", "CASE-B"),
        trials_per_case=2,
        contract=contract(),
    )
    assert a.plan_sha256 == b.plan_sha256


def test_empty_plan_is_rejected():
    with pytest.raises(ValidationError):
        TrialPlan(
            run_id="RUN",
            providers=(),
            case_ids=("CASE",),
            trials_per_case=1,
            contract_id="c",
        )


def test_duplicate_provider_is_rejected():
    with pytest.raises(ValidationError):
        TrialPlan(
            run_id="RUN",
            providers=(("p", "m"), ("p", "m")),
            case_ids=("CASE",),
            trials_per_case=1,
            contract_id="c",
        )


def test_empty_ledger_is_resumable():
    ledger = ObservationLedger(plan(), ())
    assert ledger.completed == 0
    assert ledger.remaining == 8
    assert not ledger.complete
    assert len(ledger.missing_trials()) == 8


def test_ledger_accepts_completed_observation():
    trial = plan().iter_trials()[0]
    ledger = ObservationLedger(plan(), (completed_record(trial),))
    assert ledger.completed == 1
    assert ledger.remaining == 7


def test_ledger_accepts_provider_error_observation():
    trial = plan().iter_trials()[0]
    ledger = ObservationLedger(plan(), (error_record(trial),))
    assert ledger.completed == 1


def test_ledger_rejects_duplicate_observation():
    trial = plan().iter_trials()[0]
    record = completed_record(trial)
    with pytest.raises(ValidationError):
        ObservationLedger(plan(), (record, record))


def test_ledger_rejects_foreign_observation_id():
    trial = plan().iter_trials()[0]
    record = completed_record(trial)
    foreign = BehavioralEvaluationRecord(
        observation_id="OBS-" + "F" * 24,
        contract_id=record.contract_id,
        case_id=record.case_id,
        trial_index=record.trial_index,
        provider=record.provider,
        model=record.model,
        execution_status=ProviderExecutionStatus.COMPLETED,
        evaluation_disposition=EvaluationDisposition.EVALUATED,
        passed=True,
        score=100,
    )
    with pytest.raises(ValidationError):
        ObservationLedger(plan(), (foreign,))


def test_ledger_rejects_trial_field_mismatch():
    trial = plan().iter_trials()[0]
    record = BehavioralEvaluationRecord(
        observation_id=trial.observation_id,
        contract_id=trial.contract_id,
        case_id=trial.case_id,
        trial_index=trial.trial_index,
        provider=trial.provider,
        model="wrong-model",
        execution_status=ProviderExecutionStatus.COMPLETED,
        evaluation_disposition=EvaluationDisposition.EVALUATED,
        passed=True,
        score=100,
    )
    with pytest.raises(ValidationError):
        ObservationLedger(plan(), (record,))


def test_with_record_returns_new_ledger():
    p = plan()
    empty = ObservationLedger(p, ())
    trial = p.iter_trials()[0]
    updated = empty.with_record(completed_record(trial))
    assert empty.completed == 0
    assert updated.completed == 1


def test_merge_ledgers_is_idempotent():
    p = plan()
    trial = p.iter_trials()[0]
    record = completed_record(trial)
    a = ObservationLedger(p, (record,))
    b = ObservationLedger(p, (record,))
    merged = merge_ledgers((a, b))
    assert merged.completed == 1


def test_merge_ledgers_rejects_conflict():
    p = plan()
    trial = p.iter_trials()[0]
    a = ObservationLedger(p, (completed_record(trial, score=100),))
    b = ObservationLedger(p, (completed_record(trial, score=0),))
    with pytest.raises(ValidationError):
        merge_ledgers((a, b))


def test_manifest_tracks_completion():
    p = plan()
    ledger = ObservationLedger(p, ())
    manifest = RepeatedTrialRunManifest(p, ledger)
    payload = manifest.to_dict()
    assert payload["planned_observations"] == 8
    assert payload["recorded_observations"] == 0
    assert payload["remaining_observations"] == 8
    assert payload["complete"] is False


def test_manifest_hash_is_deterministic():
    p = plan()
    a = RepeatedTrialRunManifest(p, ObservationLedger(p, ()))
    b = RepeatedTrialRunManifest(p, ObservationLedger(p, ()))
    assert a.manifest_sha256 == b.manifest_sha256
