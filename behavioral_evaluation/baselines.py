from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from kernel.exceptions import ValidationError

from .fingerprints import BehavioralFingerprint


@dataclass(frozen=True, slots=True)
class FingerprintBaseline:
    baseline_id: str
    fingerprint: BehavioralFingerprint

    def __post_init__(self) -> None:
        if not isinstance(self.baseline_id, str) or not self.baseline_id.strip():
            raise ValidationError("baseline_id must be non-empty text.")
        if not isinstance(self.fingerprint, BehavioralFingerprint):
            raise ValidationError(
                "fingerprint must be BehavioralFingerprint."
            )
        object.__setattr__(self, "baseline_id", self.baseline_id.strip())

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "g7.0",
            "baseline_id": self.baseline_id,
            "fingerprint_sha256": self.fingerprint.fingerprint_sha256,
            "provider": self.fingerprint.provider,
            "model": self.fingerprint.model,
            "schema_sha256": self.fingerprint.schema_sha256,
        }


class FingerprintBaselineRegistry:
    """Deterministic registry of named G6 reference fingerprints."""

    def __init__(
        self,
        baselines: Iterable[FingerprintBaseline] = (),
    ) -> None:
        self._items: dict[str, FingerprintBaseline] = {}
        for baseline in baselines:
            self.register(baseline)

    def register(self, baseline: FingerprintBaseline) -> None:
        if not isinstance(baseline, FingerprintBaseline):
            raise ValidationError("baseline must be FingerprintBaseline.")
        if baseline.baseline_id in self._items:
            raise ValidationError(
                f"baseline already registered: {baseline.baseline_id}"
            )
        self._items[baseline.baseline_id] = baseline

    def get(self, baseline_id: str) -> FingerprintBaseline:
        key = baseline_id.strip() if isinstance(baseline_id, str) else ""
        if not key:
            raise ValidationError("baseline_id must be non-empty text.")
        try:
            return self._items[key]
        except KeyError as exc:
            raise KeyError(f"unknown fingerprint baseline: {key}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "g7.0",
            "baselines": [
                self._items[key].to_dict()
                for key in self.names()
            ],
        }
