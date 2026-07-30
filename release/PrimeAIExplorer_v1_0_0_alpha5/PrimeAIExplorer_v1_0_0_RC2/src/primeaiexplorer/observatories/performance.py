"""Performance Observatory for canonical PrimeAIExplorer prediction records."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from statistics import mean, median
from typing import Any

from ..metrics import (
    brier_score,
    exact_accuracy,
    expected_calibration_error,
    normalized_entropy,
    shannon_entropy,
)
from .base import Observatory
from .result import ObservatoryResult


class PerformanceObservatory(Observatory):
    """Measure prediction correctness, confidence, calibration, and coverage."""

    name = "performance"
    version = "1.0.0"

    def __init__(self, *, calibration_bins: int = 10) -> None:
        if isinstance(calibration_bins, bool) or not isinstance(calibration_bins, int):
            raise TypeError("calibration_bins must be an integer.")
        if calibration_bins < 1:
            raise ValueError("calibration_bins must be positive.")
        self.calibration_bins = calibration_bins

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
    ) -> ObservatoryResult:
        normalized = [self._normalize_record(record, i) for i, record in enumerate(records, 1)]
        confidences = [row["confidence"] for row in normalized]
        correct = [row["correct"] for row in normalized]
        predictions = [row["prediction"] for row in normalized]
        signed_errors = [row["prediction"] - row["truth"] for row in normalized]
        absolute_errors = [abs(value) for value in signed_errors]

        ece, calibration = expected_calibration_error(
            confidences,
            correct,
            bins=self.calibration_bins,
        )

        dataset_case_count = self._optional_nonnegative_int(
            context.get("dataset_case_count"),
            field="dataset_case_count",
        )
        ledger_entry_count = self._optional_nonnegative_int(
            context.get("ledger_entry_count", context.get("ledger_entries")),
            field="ledger_entry_count",
        )
        pending_entry_count = self._optional_nonnegative_int(
            context.get("pending_entry_count", context.get("pending_entries")),
            field="pending_entry_count",
        ) or 0

        count = len(normalized)
        coverage = count / dataset_case_count if dataset_case_count else None
        pilot_completion = count / ledger_entry_count if ledger_entry_count else None

        metrics = {
            "record_count": count,
            "correct_count": sum(correct),
            "incorrect_count": count - sum(correct),
            "accuracy": exact_accuracy(correct),
            "mean_confidence": mean(confidences) if confidences else 0.0,
            "median_confidence": median(confidences) if confidences else 0.0,
            "brier_score": brier_score(confidences, correct),
            "ece": ece,
            "prediction_entropy_bits": shannon_entropy(predictions),
            "normalized_prediction_entropy": normalized_entropy(predictions),
            "distinct_predictions": len(set(predictions)),
            "mean_signed_error": mean(signed_errors) if signed_errors else 0.0,
            "mean_absolute_error": mean(absolute_errors) if absolute_errors else 0.0,
            "median_absolute_error": median(absolute_errors) if absolute_errors else 0.0,
            "exact_error_rate": sum(value == 0 for value in signed_errors) / count if count else 0.0,
            "dataset_case_count": dataset_case_count,
            "dataset_coverage": coverage,
            "ledger_entry_count": ledger_entry_count,
            "pending_entry_count": pending_entry_count,
            "pilot_completion": pilot_completion,
        }

        warnings: list[str] = []
        if not normalized:
            warnings.append("No completed prediction records were available.")
        if dataset_case_count is not None and count > dataset_case_count:
            warnings.append("Completed record count exceeds dataset_case_count.")
        if ledger_entry_count is not None and count > ledger_entry_count:
            warnings.append("Completed record count exceeds ledger_entry_count.")

        return ObservatoryResult(
            name=self.name,
            version=self.version,
            summary={
                "status": "complete",
                "record_count": count,
                "accuracy": metrics["accuracy"],
                "brier_score": metrics["brier_score"],
                "ece": metrics["ece"],
            },
            metrics=metrics,
            tables={
                "calibration_bins": calibration,
                "window_performance": self._window_rows(normalized),
            },
            metadata={
                "calibration_bin_count": self.calibration_bins,
                "experiment_id": context.get("experiment_id"),
                "pilot_id": context.get("pilot_id"),
                "model": context.get("model"),
            },
            warnings=warnings,
        )

    @staticmethod
    def _normalize_record(record: Mapping[str, Any], index: int) -> dict[str, Any]:
        prediction = PerformanceObservatory._required_int(record.get("prediction"), f"record {index} prediction")
        confidence = PerformanceObservatory._required_int(record.get("confidence"), f"record {index} confidence")
        if not 0 <= confidence <= 100:
            raise ValueError(f"record {index} confidence must be between 0 and 100.")

        truth_value = record.get("actual_gap")
        if truth_value is None:
            truth_value = record.get("ground_truth", record.get("truth"))
        truth = PerformanceObservatory._required_int(truth_value, f"record {index} truth")

        supplied_correct = record.get("correct")
        inferred_correct = prediction == truth
        if supplied_correct is None:
            correct = inferred_correct
        elif not isinstance(supplied_correct, bool):
            raise TypeError(f"record {index} correct must be a boolean.")
        elif supplied_correct != inferred_correct:
            raise ValueError(f"record {index} correct conflicts with prediction and truth.")
        else:
            correct = supplied_correct

        window = record.get("window", record.get("window_size"))
        if window is not None:
            window = PerformanceObservatory._required_int(window, f"record {index} window")
            if window < 1:
                raise ValueError(f"record {index} window must be positive.")

        return {
            "case_id": str(record.get("case_id", f"record-{index}")),
            "prediction": prediction,
            "confidence": confidence,
            "truth": truth,
            "correct": correct,
            "window": window,
        }

    @staticmethod
    def _required_int(value: Any, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{field} must be an integer.")
        return value

    @staticmethod
    def _optional_nonnegative_int(value: Any, *, field: str) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{field} must be an integer or None.")
        if value < 0:
            raise ValueError(f"{field} must not be negative.")
        return value

    @staticmethod
    def _window_rows(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[int | None, list[Mapping[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[record["window"]].append(record)

        rows: list[dict[str, Any]] = []
        for window, selected in sorted(grouped.items(), key=lambda item: (-1 if item[0] is None else item[0])):
            confidences = [row["confidence"] for row in selected]
            correct = [row["correct"] for row in selected]
            predictions = [row["prediction"] for row in selected]
            errors = [row["prediction"] - row["truth"] for row in selected]
            rows.append({
                "window": window,
                "count": len(selected),
                "accuracy": exact_accuracy(correct),
                "mean_confidence": mean(confidences),
                "brier_score": brier_score(confidences, correct),
                "prediction_entropy_bits": shannon_entropy(predictions),
                "mean_signed_error": mean(errors),
                "mean_absolute_error": mean(abs(value) for value in errors),
            })
        return rows
