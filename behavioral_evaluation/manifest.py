from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kernel.serialization import stable_sha256

from .observations import ObservationLedger
from .trials import TrialPlan


@dataclass(frozen=True, slots=True)
class RepeatedTrialRunManifest:
    """Deterministic run manifest for the Phase G2 observation boundary."""

    plan: TrialPlan
    ledger: ObservationLedger

    def __post_init__(self) -> None:
        if self.plan.plan_sha256 != self.ledger.plan.plan_sha256:
            raise ValueError("manifest plan and ledger plan differ.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g2.0",
            "run_id": self.plan.run_id,
            "contract_id": self.plan.contract_id,
            "plan_sha256": self.plan.plan_sha256,
            "ledger_sha256": self.ledger.ledger_sha256,
            "planned_observations": self.ledger.planned,
            "recorded_observations": self.ledger.completed,
            "remaining_observations": self.ledger.remaining,
            "complete": self.ledger.complete,
        }

    @property
    def manifest_sha256(self) -> str:
        return stable_sha256(self.to_dict())
