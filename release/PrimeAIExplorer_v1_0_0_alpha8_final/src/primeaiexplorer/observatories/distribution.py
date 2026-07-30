"""Distribution Observatory for prediction, truth, and error spectra."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from statistics import mean, median
from typing import Any

from ..metrics import normalized_entropy, shannon_entropy
from .base import Observatory
from .result import ObservatoryResult


class DistributionObservatory(Observatory):
    """Measure prediction/truth spectra, signed errors, and confusion structure."""

    name = "distribution"
    version = "1.0.0"

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
    ) -> ObservatoryResult:
        normalized = [self._normalize_record(record, i) for i, record in enumerate(records, 1)]
        predictions = [row["prediction"] for row in normalized]
        truths = [row["truth"] for row in normalized]
        errors = [row["prediction"] - row["truth"] for row in normalized]
        absolute_errors = [abs(value) for value in errors]

        prediction_counts = Counter(predictions)
        truth_counts = Counter(truths)
        error_counts = Counter(errors)
        total = len(normalized)

        support = sorted(set(prediction_counts) | set(truth_counts))
        prediction_probabilities = [prediction_counts[value] / total for value in support] if total else []
        truth_probabilities = [truth_counts[value] / total for value in support] if total else []
        total_variation = 0.5 * sum(abs(p - q) for p, q in zip(prediction_probabilities, truth_probabilities))
        js_divergence = self._jensen_shannon(prediction_probabilities, truth_probabilities)

        exact_count = sum(value == 0 for value in errors)
        under_count = sum(value < 0 for value in errors)
        over_count = sum(value > 0 for value in errors)

        metrics = {
            "record_count": total,
            "distinct_prediction_count": len(prediction_counts),
            "distinct_truth_count": len(truth_counts),
            "prediction_entropy_bits": shannon_entropy(predictions),
            "truth_entropy_bits": shannon_entropy(truths),
            "normalized_prediction_entropy": normalized_entropy(predictions),
            "normalized_truth_entropy": normalized_entropy(truths),
            "mean_signed_error": mean(errors) if errors else 0.0,
            "median_signed_error": median(errors) if errors else 0.0,
            "mean_absolute_error": mean(absolute_errors) if absolute_errors else 0.0,
            "median_absolute_error": median(absolute_errors) if absolute_errors else 0.0,
            "maximum_absolute_error": max(absolute_errors, default=0),
            "exact_count": exact_count,
            "underprediction_count": under_count,
            "overprediction_count": over_count,
            "exact_rate": exact_count / total if total else 0.0,
            "underprediction_rate": under_count / total if total else 0.0,
            "overprediction_rate": over_count / total if total else 0.0,
            "total_variation_distance": total_variation,
            "jensen_shannon_divergence_bits": js_divergence,
        }

        warnings = [] if normalized else ["No completed prediction records were available."]
        return ObservatoryResult(
            name=self.name,
            version=self.version,
            summary={
                "status": "complete",
                "record_count": total,
                "mean_absolute_error": metrics["mean_absolute_error"],
                "total_variation_distance": total_variation,
                "jensen_shannon_divergence_bits": js_divergence,
            },
            metrics=metrics,
            tables={
                "prediction_distribution": self._frequency_rows(prediction_counts, total, "prediction"),
                "truth_distribution": self._frequency_rows(truth_counts, total, "truth"),
                "error_distribution": self._frequency_rows(error_counts, total, "signed_error"),
                "confusion_matrix": self._confusion_rows(normalized),
                "window_distribution": self._window_rows(normalized),
            },
            metadata={
                "experiment_id": context.get("experiment_id"),
                "pilot_id": context.get("pilot_id"),
                "model": context.get("model"),
            },
            warnings=warnings,
        )

    @staticmethod
    def _normalize_record(record: Mapping[str, Any], index: int) -> dict[str, Any]:
        prediction = record.get("prediction")
        truth = record.get("actual_gap", record.get("ground_truth", record.get("truth")))
        if isinstance(prediction, bool) or not isinstance(prediction, int):
            raise TypeError(f"record {index} prediction must be an integer.")
        if isinstance(truth, bool) or not isinstance(truth, int):
            raise TypeError(f"record {index} truth must be an integer.")
        window = record.get("window", record.get("window_size"))
        if window is not None and (isinstance(window, bool) or not isinstance(window, int) or window < 1):
            raise ValueError(f"record {index} window must be a positive integer or None.")
        return {"prediction": prediction, "truth": truth, "window": window}

    @staticmethod
    def _frequency_rows(counts: Counter[int], total: int, field: str) -> list[dict[str, Any]]:
        return [
            {field: value, "count": count, "share": count / total if total else 0.0}
            for value, count in sorted(counts.items())
        ]

    @staticmethod
    def _confusion_rows(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        counts = Counter((row["truth"], row["prediction"]) for row in records)
        truth_totals = Counter(row["truth"] for row in records)
        return [
            {
                "truth": truth,
                "prediction": prediction,
                "count": count,
                "conditional_share": count / truth_totals[truth],
            }
            for (truth, prediction), count in sorted(counts.items())
        ]

    @staticmethod
    def _window_rows(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[int | None, list[Mapping[str, Any]]] = defaultdict(list)
        for row in records:
            grouped[row["window"]].append(row)
        output: list[dict[str, Any]] = []
        for window, rows in sorted(grouped.items(), key=lambda item: (-1 if item[0] is None else item[0])):
            predictions = [row["prediction"] for row in rows]
            truths = [row["truth"] for row in rows]
            errors = [p - t for p, t in zip(predictions, truths)]
            output.append({
                "window": window,
                "count": len(rows),
                "distinct_predictions": len(set(predictions)),
                "distinct_truths": len(set(truths)),
                "prediction_entropy_bits": shannon_entropy(predictions),
                "truth_entropy_bits": shannon_entropy(truths),
                "mean_signed_error": mean(errors),
                "mean_absolute_error": mean(abs(value) for value in errors),
            })
        return output

    @staticmethod
    def _jensen_shannon(p: Sequence[float], q: Sequence[float]) -> float:
        if not p:
            return 0.0
        m = [(a + b) / 2.0 for a, b in zip(p, q)]

        def kl(a: Sequence[float], b: Sequence[float]) -> float:
            return sum(x * math.log2(x / y) for x, y in zip(a, b) if x > 0 and y > 0)

        return 0.5 * kl(p, m) + 0.5 * kl(q, m)
