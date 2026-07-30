"""Surprise Observatory for rare, novel, and unexpected prediction events."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from statistics import mean
from typing import Any

from .base import Observatory
from .result import ObservatoryResult


class SurpriseObservatory(Observatory):
    """Measure event rarity, novelty, confidence surprise, and transition surprise.

    The composite surprise index is deliberately descriptive rather than
    probabilistic.  Each record receives four non-negative components:

    * truth rarity: ``-log2(P(truth))``;
    * prediction rarity: ``-log2(P(prediction))``;
    * confidence surprise: ``abs(confidence - correctness)``;
    * error surprise: ``log2(1 + absolute_error)``.

    For records after the first, transition surprise ``-log2(P(next|current))``
    is also included.  The composite index is the arithmetic mean of the
    available components, keeping the calculation interpretable and stable.
    """

    name = "surprise"
    version = "1.0.0"

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
    ) -> ObservatoryResult:
        rows = [self._normalize_record(record, index) for index, record in enumerate(records, 1)]
        total = len(rows)
        prediction_counts = Counter(row["prediction"] for row in rows)
        truth_counts = Counter(row["truth"] for row in rows)
        transition_counts = Counter(
            (rows[index - 1]["prediction"], rows[index]["prediction"])
            for index in range(1, total)
        )
        transition_totals = Counter(source for source, _ in transition_counts)

        event_rows: list[dict[str, Any]] = []
        seen_predictions: set[int] = set()
        novel_rows: list[dict[str, Any]] = []

        for index, row in enumerate(rows, 1):
            prediction_probability = prediction_counts[row["prediction"]] / total if total else 0.0
            truth_probability = truth_counts[row["truth"]] / total if total else 0.0
            prediction_rarity = self._information_bits(prediction_probability)
            truth_rarity = self._information_bits(truth_probability)
            correctness = 1.0 if row["prediction"] == row["truth"] else 0.0
            confidence_surprise = abs(row["confidence"] - correctness)
            absolute_error = abs(row["prediction"] - row["truth"])
            error_surprise = math.log2(1.0 + absolute_error)

            transition_probability: float | None = None
            transition_surprise: float | None = None
            previous_prediction: int | None = None
            if index > 1:
                previous_prediction = rows[index - 2]["prediction"]
                transition_probability = (
                    transition_counts[(previous_prediction, row["prediction"])]
                    / transition_totals[previous_prediction]
                )
                transition_surprise = self._information_bits(transition_probability)

            components = [truth_rarity, prediction_rarity, confidence_surprise, error_surprise]
            if transition_surprise is not None:
                components.append(transition_surprise)
            surprise_index = mean(components)
            is_novel = row["prediction"] not in seen_predictions
            if is_novel:
                novel_rows.append({
                    "record_index": index,
                    "case_id": row["case_id"],
                    "window": row["window"],
                    "prediction": row["prediction"],
                    "confidence": row["confidence"],
                })
                seen_predictions.add(row["prediction"])

            event_rows.append({
                "record_index": index,
                "case_id": row["case_id"],
                "window": row["window"],
                "prediction": row["prediction"],
                "truth": row["truth"],
                "confidence": row["confidence"],
                "correct": bool(correctness),
                "absolute_error": absolute_error,
                "novel_prediction": is_novel,
                "truth_rarity_bits": truth_rarity,
                "prediction_rarity_bits": prediction_rarity,
                "confidence_surprise": confidence_surprise,
                "error_surprise_bits": error_surprise,
                "previous_prediction": previous_prediction,
                "transition_probability": transition_probability,
                "transition_surprise_bits": transition_surprise,
                "surprise_index": surprise_index,
            })

        ranked = sorted(event_rows, key=lambda row: (-row["surprise_index"], row["record_index"]))
        rank_by_index = {row["record_index"]: rank for rank, row in enumerate(ranked, 1)}
        for row in event_rows:
            row["surprise_rank"] = rank_by_index[row["record_index"]]

        indices = [row["surprise_index"] for row in event_rows]
        confidence_surprises = [row["confidence_surprise"] for row in event_rows]
        unexpected_errors = [row for row in event_rows if not row["correct"]]
        transition_rows = self._transition_rows(transition_counts, transition_totals)

        metrics = {
            "record_count": total,
            "novel_prediction_count": len(novel_rows),
            "novel_prediction_rate": len(novel_rows) / total if total else 0.0,
            "mean_surprise_index": mean(indices) if indices else 0.0,
            "maximum_surprise_index": max(indices, default=0.0),
            "mean_confidence_surprise": mean(confidence_surprises) if confidence_surprises else 0.0,
            "unexpected_error_count": len(unexpected_errors),
            "unexpected_error_rate": len(unexpected_errors) / total if total else 0.0,
            "distinct_prediction_count": len(prediction_counts),
            "distinct_truth_count": len(truth_counts),
            "mean_truth_rarity_bits": mean(row["truth_rarity_bits"] for row in event_rows) if event_rows else 0.0,
            "mean_prediction_rarity_bits": mean(row["prediction_rarity_bits"] for row in event_rows) if event_rows else 0.0,
            "mean_transition_surprise_bits": mean(
                row["transition_surprise_bits"]
                for row in event_rows
                if row["transition_surprise_bits"] is not None
            ) if total > 1 else 0.0,
        }

        warnings = [] if rows else ["No completed prediction records were available."]
        return ObservatoryResult(
            name=self.name,
            version=self.version,
            summary={
                "status": "complete",
                "record_count": total,
                "mean_surprise_index": metrics["mean_surprise_index"],
                "maximum_surprise_index": metrics["maximum_surprise_index"],
                "novel_prediction_rate": metrics["novel_prediction_rate"],
            },
            metrics=metrics,
            tables={
                "surprise_events": event_rows,
                "surprise_timeline": self._timeline_rows(event_rows),
                "novel_predictions": novel_rows,
                "window_surprise": self._window_rows(event_rows),
                "unexpected_transitions": transition_rows,
                "top_surprises": ranked[: min(10, len(ranked))],
            },
            metadata={
                "experiment_id": context.get("experiment_id"),
                "pilot_id": context.get("pilot_id"),
                "model": context.get("model"),
                "formula": "mean(truth rarity, prediction rarity, confidence surprise, error surprise, optional transition surprise)",
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
        confidence = record.get("confidence", 0.0)
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise TypeError(f"record {index} confidence must be numeric.")
        confidence = float(confidence)
        if confidence > 1.0:
            confidence /= 100.0
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"record {index} confidence must be between 0 and 1 or 0 and 100.")
        window = record.get("window", record.get("window_size"))
        if window is not None and (isinstance(window, bool) or not isinstance(window, int) or window < 1):
            raise ValueError(f"record {index} window must be a positive integer or None.")
        return {
            "case_id": record.get("case_id", f"record-{index}"),
            "window": window,
            "prediction": prediction,
            "truth": truth,
            "confidence": confidence,
        }

    @staticmethod
    def _information_bits(probability: float) -> float:
        return -math.log2(probability) if probability > 0.0 else 0.0

    @staticmethod
    def _timeline_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        cumulative: list[float] = []
        output: list[dict[str, Any]] = []
        for row in events:
            cumulative.append(float(row["surprise_index"]))
            output.append({
                "record_index": row["record_index"],
                "case_id": row["case_id"],
                "window": row["window"],
                "surprise_index": row["surprise_index"],
                "cumulative_mean_surprise": mean(cumulative),
                "cumulative_max_surprise": max(cumulative),
            })
        return output

    @staticmethod
    def _window_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[int | None, list[Mapping[str, Any]]] = defaultdict(list)
        for row in events:
            grouped[row["window"]].append(row)
        output: list[dict[str, Any]] = []
        for window, rows in sorted(grouped.items(), key=lambda item: (-1 if item[0] is None else item[0])):
            values = [float(row["surprise_index"]) for row in rows]
            output.append({
                "window": window,
                "count": len(rows),
                "mean_surprise_index": mean(values),
                "maximum_surprise_index": max(values),
                "novel_prediction_rate": sum(bool(row["novel_prediction"]) for row in rows) / len(rows),
                "unexpected_error_rate": sum(not bool(row["correct"]) for row in rows) / len(rows),
            })
        return output

    @staticmethod
    def _transition_rows(
        counts: Counter[tuple[int, int]],
        totals: Counter[int],
    ) -> list[dict[str, Any]]:
        return [
            {
                "from_prediction": source,
                "to_prediction": target,
                "count": count,
                "probability": count / totals[source],
                "surprise_bits": -math.log2(count / totals[source]),
            }
            for (source, target), count in sorted(counts.items())
        ]
