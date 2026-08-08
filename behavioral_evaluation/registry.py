from __future__ import annotations

from collections.abc import Iterable

from kernel.exceptions import ValidationError

from .contracts import BehavioralEvaluationContract


class BehavioralEvaluationContractRegistry:
    def __init__(self, contracts: Iterable[BehavioralEvaluationContract] = ()) -> None:
        self._contracts: dict[str, BehavioralEvaluationContract] = {}
        for contract in contracts:
            self.register(contract)

    def register(self, contract: BehavioralEvaluationContract) -> None:
        if not isinstance(contract, BehavioralEvaluationContract):
            raise ValidationError("contract must be BehavioralEvaluationContract.")
        if contract.contract_id in self._contracts:
            raise ValidationError(
                f"behavioral evaluation contract already registered: {contract.contract_id}"
            )
        self._contracts[contract.contract_id] = contract

    def get(self, contract_id: str) -> BehavioralEvaluationContract:
        key = contract_id.strip() if isinstance(contract_id, str) else ""
        if not key:
            raise ValidationError("contract_id must not be empty.")
        try:
            return self._contracts[key]
        except KeyError as exc:
            raise KeyError(f"unknown behavioral evaluation contract: {key}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._contracts))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "g1.0",
            "contracts": [self._contracts[key].to_dict() for key in self.names()],
        }
