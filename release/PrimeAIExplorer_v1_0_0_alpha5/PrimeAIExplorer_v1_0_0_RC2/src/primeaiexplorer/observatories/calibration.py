"""Calibration Observatory for confidence reliability analysis."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from statistics import mean
from typing import Any

from ..metrics import brier_score, exact_accuracy, expected_calibration_error
from .base import Observatory
from .result import ObservatoryResult


class CalibrationObservatory(Observatory):
    """Measure reliability, calibration bias, and confidence-bin behavior."""

    name = "calibration"
    version = "1.0.0"

    def __init__(self, *, bins: int = 10) -> None:
        if isinstance(bins, bool) or not isinstance(bins, int):
            raise TypeError("bins must be an integer.")
        if bins < 1:
            raise ValueError("bins must be positive.")
        self.bins = bins

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
    ) -> ObservatoryResult:
        normalized = [self._normalize_record(record, i) for i, record in enumerate(records, 1)]
        confidences = [row["confidence"] for row in normalized]
        correct = [row["correct"] for row in normalized]
        ece, reliability = expected_calibration_error(confidences, correct, bins=self.bins)

        for row in reliability:
            row["signed_gap"] = row["average_confidence"] - row["accuracy"]
            row["calibration_state"] = self._state(row["signed_gap"])
            row["weighted_gap"] = row["absolute_gap"] * row["count"] / len(normalized)

        accuracy = exact_accuracy(correct)
        mean_confidence = mean(confidences) / 100.0 if confidences else 0.0
        signed_bias = mean_confidence - accuracy
        maximum_calibration_error = max((row["absolute_gap"] for row in reliability), default=0.0)
        overconfident = sum(row["count"] for row in reliability if row["signed_gap"] > 0)
        underconfident = sum(row["count"] for row in reliability if row["signed_gap"] < 0)
        calibrated = sum(row["count"] for row in reliability if row["signed_gap"] == 0)

        metrics = {
            "record_count": len(normalized),
            "bin_count": self.bins,
            "occupied_bin_count": len(reliability),
            "accuracy": accuracy,
            "mean_confidence": mean_confidence,
            "signed_calibration_bias": signed_bias,
            "absolute_calibration_bias": abs(signed_bias),
            "ece": ece,
            "maximum_calibration_error": maximum_calibration_error,
            "brier_score": brier_score(confidences, correct),
            "overconfident_record_count": overconfident,
            "underconfident_record_count": underconfident,
            "exactly_calibrated_record_count": calibrated,
            "overconfidence_rate": overconfident / len(normalized) if normalized else 0.0,
            "underconfidence_rate": underconfident / len(normalized) if normalized else 0.0,
        }

        warnings: list[str] = []
        if not normalized:
            warnings.append("No completed prediction records were available.")
        if len(reliability) < min(self.bins, 3) and normalized:
            warnings.append("Few confidence bins are occupied; calibration estimates may be coarse.")

        return ObservatoryResult(
            name=self.name,
            version=self.version,
            summary={
                "status": "complete",
                "record_count": len(normalized),
                "ece": ece,
                "maximum_calibration_error": maximum_calibration_error,
                "signed_calibration_bias": signed_bias,
            },
            metrics=metrics,
            tables={
                "reliability_bins": reliability,
                "window_calibration": self._window_rows(normalized),
            },
            metadata={
                "configured_bin_count": self.bins,
                "experiment_id": context.get("experiment_id"),
                "pilot_id": context.get("pilot_id"),
                "model": context.get("model"),
            },
            warnings=warnings,
        )

    @staticmethod
    def _state(signed_gap: float) -> str:
        if signed_gap > 1e-12:
            return "overconfident"
        if signed_gap < -1e-12:
            return "underconfident"
        return "calibrated"

    @staticmethod
    def _normalize_record(record: Mapping[str, Any], index: int) -> dict[str, Any]:
        confidence = record.get("confidence")
        prediction = record.get("prediction")
        truth = record.get("actual_gap", record.get("ground_truth", record.get("truth")))
        if isinstance(confidence, bool) or not isinstance(confidence, int):
            raise TypeError(f"record {index} confidence must be an integer.")
        if not 0 <= confidence <= 100:
            raise ValueError(f"record {index} confidence must be between 0 and 100.")
        if isinstance(prediction, bool) or not isinstance(prediction, int):
            raise TypeError(f"record {index} prediction must be an integer.")
        if isinstance(truth, bool) or not isinstance(truth, int):
            raise TypeError(f"record {index} truth must be an integer.")
        inferred = prediction == truth
        supplied = record.get("correct")
        if supplied is not None and not isinstance(supplied, bool):
            raise TypeError(f"record {index} correct must be a boolean.")
        if supplied is not None and supplied != inferred:
            raise ValueError(f"record {index} correct conflicts with prediction and truth.")
        window = record.get("window", record.get("window_size"))
        if window is not None and (isinstance(window, bool) or not isinstance(window, int) or window < 1):
            raise ValueError(f"record {index} window must be a positive integer or None.")
        return {"confidence": confidence, "correct": inferred, "window": window}

    def _window_rows(self, records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[int | None, list[Mapping[str, Any]]] = defaultdict(list)
        for row in records:
            grouped[row["window"]].append(row)
        output: list[dict[str, Any]] = []
        for window, rows in sorted(grouped.items(), key=lambda item: (-1 if item[0] is None else item[0])):
            confidences = [row["confidence"] for row in rows]
            correct = [row["correct"] for row in rows]
            ece, _ = expected_calibration_error(confidences, correct, bins=self.bins)
            accuracy = exact_accuracy(correct)
            average_confidence = mean(confidences) / 100.0
            output.append({
                "window": window,
                "count": len(rows),
                "accuracy": accuracy,
                "mean_confidence": average_confidence,
                "signed_calibration_bias": average_confidence - accuracy,
                "ece": ece,
                "brier_score": brier_score(confidences, correct),
            })
        return output
