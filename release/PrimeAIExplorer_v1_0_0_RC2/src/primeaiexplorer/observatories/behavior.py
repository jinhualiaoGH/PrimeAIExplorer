"""Behavior Observatory for sequential PrimeAIExplorer predictions."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from statistics import mean
from typing import Any

from ..metrics import normalized_entropy, shannon_entropy
from .base import Observatory
from .result import ObservatoryResult


class BehaviorObservatory(Observatory):
    """Measure popularity, persistence, switching, transitions, and fingerprint."""

    name = "behavior"
    version = "1.0.0"

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
    ) -> ObservatoryResult:
        normalized = [self._normalize_record(record, i) for i, record in enumerate(records, 1)]
        predictions = [row["prediction"] for row in normalized]
        counts = Counter(predictions)
        popularity = self._popularity_rows(counts, len(predictions))
        runs = self._run_rows(normalized)
        transitions = self._transition_rows(predictions)

        switch_count = sum(a != b for a, b in zip(predictions, predictions[1:]))
        transition_count = max(len(predictions) - 1, 0)
        switch_rate = switch_count / transition_count if transition_count else 0.0
        repeat_count = transition_count - switch_count
        repeat_rate = repeat_count / transition_count if transition_count else 0.0
        run_lengths = [row["length"] for row in runs]

        favorite_prediction = popularity[0]["prediction"] if popularity else None
        favorite_count = popularity[0]["count"] if popularity else 0
        favorite_share = popularity[0]["frequency"] if popularity else 0.0

        confidences = [row["confidence"] for row in normalized if row["confidence"] is not None]
        correct_values = [row["correct"] for row in normalized if row["correct"] is not None]
        confidence_correct_pairs = [
            (row["confidence"], row["correct"])
            for row in normalized
            if row["confidence"] is not None and row["correct"] is not None
        ]
        mean_confidence = mean(confidences) if confidences else None
        empirical_accuracy = mean(float(value) for value in correct_values) if correct_values else None
        confidence_realism_gap = (
            abs(mean(c / 100.0 for c, _ in confidence_correct_pairs) - mean(float(y) for _, y in confidence_correct_pairs))
            if confidence_correct_pairs
            else None
        )

        metrics = {
            "record_count": len(normalized),
            "distinct_predictions": len(counts),
            "favorite_prediction": favorite_prediction,
            "favorite_prediction_count": favorite_count,
            "favorite_prediction_share": favorite_share,
            "prediction_entropy_bits": shannon_entropy(predictions),
            "normalized_prediction_entropy": normalized_entropy(predictions),
            "transition_count": transition_count,
            "switch_count": switch_count,
            "switch_rate": switch_rate,
            "repeat_count": repeat_count,
            "repeat_rate": repeat_rate,
            "run_count": len(runs),
            "mean_run_length": mean(run_lengths) if run_lengths else 0.0,
            "max_run_length": max(run_lengths, default=0),
            "min_run_length": min(run_lengths, default=0),
            "mean_confidence": mean_confidence,
            "empirical_accuracy": empirical_accuracy,
            "confidence_realism_gap": confidence_realism_gap,
        }

        fingerprint = self._fingerprint_rows(metrics)
        warnings: list[str] = []
        if not normalized:
            warnings.append("No completed prediction records were available.")
        if len(normalized) == 1:
            warnings.append("Switching metrics require at least two records; zero values were returned.")
        if not confidences:
            warnings.append("Confidence fields were unavailable; confidence fingerprint metrics are null.")
        if not correct_values:
            warnings.append("Correctness fields were unavailable; accuracy fingerprint metrics are null.")

        return ObservatoryResult(
            name=self.name,
            version=self.version,
            summary={
                "status": "complete",
                "record_count": len(normalized),
                "favorite_prediction": favorite_prediction,
                "switch_rate": switch_rate,
                "max_run_length": metrics["max_run_length"],
            },
            metrics=metrics,
            tables={
                "prediction_popularity": popularity,
                "persistence_runs": runs,
                "prediction_transitions": transitions,
                "window_behavior": self._window_rows(normalized),
                "behavior_fingerprint": fingerprint,
            },
            metadata={
                "sequence_order": "input_order",
                "experiment_id": context.get("experiment_id"),
                "pilot_id": context.get("pilot_id"),
                "model": context.get("model"),
            },
            warnings=warnings,
        )

    @staticmethod
    def _normalize_record(record: Mapping[str, Any], index: int) -> dict[str, Any]:
        prediction = BehaviorObservatory._required_int(record.get("prediction"), f"record {index} prediction")

        confidence = record.get("confidence")
        if confidence is not None:
            confidence = BehaviorObservatory._required_int(confidence, f"record {index} confidence")
            if not 0 <= confidence <= 100:
                raise ValueError(f"record {index} confidence must be between 0 and 100.")

        correct = record.get("correct")
        if correct is not None and not isinstance(correct, bool):
            raise TypeError(f"record {index} correct must be a boolean or None.")

        truth = record.get("actual_gap")
        if truth is None:
            truth = record.get("ground_truth", record.get("truth"))
        if truth is not None:
            truth = BehaviorObservatory._required_int(truth, f"record {index} truth")
            inferred = prediction == truth
            if correct is None:
                correct = inferred
            elif correct != inferred:
                raise ValueError(f"record {index} correct conflicts with prediction and truth.")

        window = record.get("window", record.get("window_size"))
        if window is not None:
            window = BehaviorObservatory._required_int(window, f"record {index} window")
            if window < 1:
                raise ValueError(f"record {index} window must be positive.")

        return {
            "case_id": str(record.get("case_id", f"record-{index}")),
            "sequence_number": index,
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
    def _popularity_rows(counts: Counter[int], total: int) -> list[dict[str, Any]]:
        return [
            {
                "rank": rank,
                "prediction": prediction,
                "count": count,
                "frequency": count / total if total else 0.0,
            }
            for rank, (prediction, count) in enumerate(
                sorted(counts.items(), key=lambda item: (-item[1], item[0])), start=1
            )
        ]

    @staticmethod
    def _run_rows(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        if not records:
            return []
        rows: list[dict[str, Any]] = []
        start = 0
        run_number = 1
        for index in range(1, len(records) + 1):
            boundary = index == len(records) or records[index]["prediction"] != records[start]["prediction"]
            if boundary:
                rows.append({
                    "run": run_number,
                    "prediction": records[start]["prediction"],
                    "start_n": start + 1,
                    "end_n": index,
                    "start_case_id": records[start]["case_id"],
                    "end_case_id": records[index - 1]["case_id"],
                    "length": index - start,
                })
                run_number += 1
                start = index
        return rows

    @staticmethod
    def _transition_rows(predictions: Sequence[int]) -> list[dict[str, Any]]:
        counts = Counter(zip(predictions, predictions[1:]))
        outgoing = Counter(a for a, _ in zip(predictions, predictions[1:]))
        return [
            {
                "from_prediction": source,
                "to_prediction": target,
                "count": count,
                "probability": count / outgoing[source],
                "is_switch": source != target,
            }
            for (source, target), count in sorted(counts.items())
        ]

    @staticmethod
    def _fingerprint_rows(metrics: Mapping[str, Any]) -> list[dict[str, Any]]:
        names = (
            "favorite_prediction",
            "favorite_prediction_share",
            "prediction_entropy_bits",
            "normalized_prediction_entropy",
            "switch_rate",
            "repeat_rate",
            "mean_run_length",
            "max_run_length",
            "mean_confidence",
            "empirical_accuracy",
            "confidence_realism_gap",
        )
        return [{"metric": name, "value": metrics[name]} for name in names]

    @classmethod
    def _window_rows(cls, records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[int | None, list[Mapping[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[record["window"]].append(record)
        rows: list[dict[str, Any]] = []
        for window, selected in sorted(grouped.items(), key=lambda item: (-1 if item[0] is None else item[0])):
            predictions = [row["prediction"] for row in selected]
            switches = sum(a != b for a, b in zip(predictions, predictions[1:]))
            transitions = max(len(predictions) - 1, 0)
            counts = Counter(predictions)
            favorite, favorite_count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
            runs = cls._run_rows(selected)
            rows.append({
                "window": window,
                "count": len(selected),
                "distinct_predictions": len(counts),
                "favorite_prediction": favorite,
                "favorite_prediction_share": favorite_count / len(selected),
                "prediction_entropy_bits": shannon_entropy(predictions),
                "switch_rate": switches / transitions if transitions else 0.0,
                "run_count": len(runs),
                "max_run_length": max((row["length"] for row in runs), default=0),
            })
        return rows
