from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256

from .contracts import BehavioralEvaluationRecord
from .trials import TrialPlan, TrialSpec


@dataclass(frozen=True, slots=True)
class ObservationLedger:
    """Immutable aggregation-ready set of G1 observation records for one G2 plan."""

    plan: TrialPlan
    records: tuple[BehavioralEvaluationRecord, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.plan, TrialPlan):
            raise ValidationError("plan must be TrialPlan.")

        records = tuple(self.records)
        object.__setattr__(self, "records", records)

        expected = {trial.observation_id: trial for trial in self.plan.iter_trials()}
        seen: set[str] = set()

        for record in records:
            if not isinstance(record, BehavioralEvaluationRecord):
                raise ValidationError(
                    "records must contain BehavioralEvaluationRecord values."
                )

            if record.observation_id not in expected:
                raise ValidationError(
                    f"observation is not part of this plan: {record.observation_id}"
                )

            if record.observation_id in seen:
                raise ValidationError(
                    f"duplicate observation_id: {record.observation_id}"
                )
            seen.add(record.observation_id)

            trial = expected[record.observation_id]
            _validate_record_against_trial(record, trial)

    @property
    def planned(self) -> int:
        return self.plan.total_trials

    @property
    def completed(self) -> int:
        return len(self.records)

    @property
    def remaining(self) -> int:
        return self.planned - self.completed

    @property
    def complete(self) -> bool:
        return self.remaining == 0

    def missing_trials(self) -> tuple[TrialSpec, ...]:
        seen = {record.observation_id for record in self.records}
        return tuple(
            trial
            for trial in self.plan.iter_trials()
            if trial.observation_id not in seen
        )

    def with_record(
        self,
        record: BehavioralEvaluationRecord,
    ) -> "ObservationLedger":
        return ObservationLedger(self.plan, self.records + (record,))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "g2.0",
            "plan_sha256": self.plan.plan_sha256,
            "planned": self.planned,
            "completed": self.completed,
            "remaining": self.remaining,
            "complete": self.complete,
            "records": [
                record.to_dict()
                for record in sorted(
                    self.records,
                    key=lambda item: item.observation_id,
                )
            ],
        }

    @property
    def ledger_sha256(self) -> str:
        return stable_sha256(self.to_dict())


def _validate_record_against_trial(
    record: BehavioralEvaluationRecord,
    trial: TrialSpec,
) -> None:
    pairs = (
        ("contract_id", record.contract_id, trial.contract_id),
        ("case_id", record.case_id, trial.case_id),
        ("trial_index", record.trial_index, trial.trial_index),
        ("provider", record.provider, trial.provider),
        ("model", record.model, trial.model),
    )
    for name, observed, expected in pairs:
        if observed != expected:
            raise ValidationError(
                f"observation {name} mismatch: "
                f"expected {expected!r}, got {observed!r}"
            )


def merge_ledgers(
    ledgers: Iterable[ObservationLedger],
) -> ObservationLedger:
    ledgers = tuple(ledgers)
    if not ledgers:
        raise ValidationError("at least one ledger is required.")

    plan = ledgers[0].plan
    if any(item.plan.plan_sha256 != plan.plan_sha256 for item in ledgers[1:]):
        raise ValidationError("all ledgers must use the same trial plan.")

    merged: dict[str, BehavioralEvaluationRecord] = {}
    for ledger in ledgers:
        for record in ledger.records:
            existing = merged.get(record.observation_id)
            if existing is not None and existing.record_sha256 != record.record_sha256:
                raise ValidationError(
                    f"conflicting observation: {record.observation_id}"
                )
            merged[record.observation_id] = record

    return ObservationLedger(
        plan=plan,
        records=tuple(merged[key] for key in sorted(merged)),
    )
