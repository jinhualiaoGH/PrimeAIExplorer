from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256

from .contracts import BehavioralEvaluationContract


def _text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be text.")
    value = value.strip()
    if not value:
        raise ValidationError(f"{name} must not be empty.")
    return value


@dataclass(frozen=True, slots=True)
class TrialSpec:
    """Immutable identity for one provider × case × trial observation."""

    run_id: str
    provider: str
    model: str
    case_id: str
    trial_index: int
    contract_id: str

    def __post_init__(self) -> None:
        for name in ("run_id", "provider", "model", "case_id", "contract_id"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        if (
            isinstance(self.trial_index, bool)
            or not isinstance(self.trial_index, int)
            or self.trial_index <= 0
        ):
            raise ValidationError("trial_index must be a positive integer.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g2.0",
            "run_id": self.run_id,
            "provider": self.provider,
            "model": self.model,
            "case_id": self.case_id,
            "trial_index": self.trial_index,
            "contract_id": self.contract_id,
        }

    @property
    def observation_id(self) -> str:
        return f"OBS-{stable_sha256(self.to_dict())[:24].upper()}"


@dataclass(frozen=True, slots=True)
class TrialPlan:
    """Deterministic repeated-trial schedule.

    Phase G2 intentionally does not invoke providers. It defines a stable,
    resumable observation schedule that an execution bridge can consume.
    """

    run_id: str
    providers: tuple[tuple[str, str], ...]
    case_ids: tuple[str, ...]
    trials_per_case: int
    contract_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _text("run_id", self.run_id))
        object.__setattr__(self, "contract_id", _text("contract_id", self.contract_id))

        if (
            isinstance(self.trials_per_case, bool)
            or not isinstance(self.trials_per_case, int)
            or self.trials_per_case <= 0
        ):
            raise ValidationError("trials_per_case must be a positive integer.")

        providers = []
        for item in self.providers:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
            ):
                raise ValidationError(
                    "providers must contain (provider, model) tuples."
                )
            provider = _text("provider", item[0])
            model = _text("model", item[1])
            providers.append((provider, model))

        case_ids = tuple(_text("case_id", item) for item in self.case_ids)

        if not providers:
            raise ValidationError("providers must not be empty.")
        if not case_ids:
            raise ValidationError("case_ids must not be empty.")

        if len(set(providers)) != len(providers):
            raise ValidationError("providers must be unique.")
        if len(set(case_ids)) != len(case_ids):
            raise ValidationError("case_ids must be unique.")

        object.__setattr__(self, "providers", tuple(providers))
        object.__setattr__(self, "case_ids", case_ids)

    @property
    def total_trials(self) -> int:
        return len(self.providers) * len(self.case_ids) * self.trials_per_case

    def iter_trials(self) -> tuple[TrialSpec, ...]:
        """Return canonical deterministic trial order.

        Ordering is provider/model, then case_id, then 1-based trial index.
        """
        items: list[TrialSpec] = []
        for provider, model in sorted(self.providers):
            for case_id in sorted(self.case_ids):
                for trial_index in range(1, self.trials_per_case + 1):
                    items.append(
                        TrialSpec(
                            run_id=self.run_id,
                            provider=provider,
                            model=model,
                            case_id=case_id,
                            trial_index=trial_index,
                            contract_id=self.contract_id,
                        )
                    )
        return tuple(items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g2.0",
            "run_id": self.run_id,
            "contract_id": self.contract_id,
            "trials_per_case": self.trials_per_case,
            "providers": [
                {"provider": provider, "model": model}
                for provider, model in sorted(self.providers)
            ],
            "case_ids": sorted(self.case_ids),
            "total_trials": self.total_trials,
        }

    @property
    def plan_sha256(self) -> str:
        return stable_sha256(self.to_dict())

    @classmethod
    def from_contract(
        cls,
        *,
        run_id: str,
        providers: Iterable[tuple[str, str]],
        case_ids: Iterable[str],
        trials_per_case: int,
        contract: BehavioralEvaluationContract,
    ) -> "TrialPlan":
        if not isinstance(contract, BehavioralEvaluationContract):
            raise ValidationError(
                "contract must be BehavioralEvaluationContract."
            )
        return cls(
            run_id=run_id,
            providers=tuple(providers),
            case_ids=tuple(case_ids),
            trials_per_case=trials_per_case,
            contract_id=contract.contract_id,
        )
