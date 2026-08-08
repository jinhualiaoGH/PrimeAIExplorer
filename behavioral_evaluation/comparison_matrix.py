from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from kernel.exceptions import ValidationError

from .fingerprint_distance import compare_fingerprints
from .fingerprints import BehavioralFingerprint


@dataclass(frozen=True, slots=True)
class FingerprintMatrixEntry:
    row_subject: str
    column_subject: str
    comparable_features: int
    euclidean_distance: float | None
    manhattan_distance: float | None
    cosine_similarity: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g7.0",
            "row_subject": self.row_subject,
            "column_subject": self.column_subject,
            "comparable_features": self.comparable_features,
            "euclidean_distance": self.euclidean_distance,
            "manhattan_distance": self.manhattan_distance,
            "cosine_similarity": self.cosine_similarity,
        }


@dataclass(frozen=True, slots=True)
class FingerprintComparisonMatrix:
    subjects: tuple[str, ...]
    entries: tuple[FingerprintMatrixEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "g7.0",
            "subjects": list(self.subjects),
            "entries": [entry.to_dict() for entry in self.entries],
        }


def subject_id(fingerprint: BehavioralFingerprint) -> str:
    return f"{fingerprint.provider}/{fingerprint.model}"


def build_comparison_matrix(
    fingerprints: Iterable[BehavioralFingerprint],
) -> FingerprintComparisonMatrix:
    values = tuple(fingerprints)
    if not values:
        return FingerprintComparisonMatrix((), ())

    for item in values:
        if not isinstance(item, BehavioralFingerprint):
            raise ValidationError(
                "comparison matrix requires BehavioralFingerprint values."
            )

    schema_hashes = {item.schema_sha256 for item in values}
    if len(schema_hashes) != 1:
        raise ValidationError(
            "comparison matrix requires a single fingerprint schema."
        )

    subjects = [subject_id(item) for item in values]
    if len(set(subjects)) != len(subjects):
        raise ValidationError(
            "comparison matrix subjects must be unique provider/model pairs."
        )

    ordered = tuple(
        sorted(values, key=lambda item: subject_id(item))
    )
    ordered_subjects = tuple(subject_id(item) for item in ordered)

    entries = []
    for row in ordered:
        for column in ordered:
            comparison = compare_fingerprints(row, column)
            entries.append(
                FingerprintMatrixEntry(
                    row_subject=subject_id(row),
                    column_subject=subject_id(column),
                    comparable_features=comparison.comparable_features,
                    euclidean_distance=comparison.euclidean_distance,
                    manhattan_distance=comparison.manhattan_distance,
                    cosine_similarity=comparison.cosine_similarity,
                )
            )

    return FingerprintComparisonMatrix(
        subjects=ordered_subjects,
        entries=tuple(entries),
    )
