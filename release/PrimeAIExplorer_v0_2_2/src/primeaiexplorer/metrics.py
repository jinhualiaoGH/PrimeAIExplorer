from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Sequence


def exact_accuracy(correct: Sequence[bool]) -> float:
    return sum(bool(x) for x in correct) / len(correct) if correct else 0.0


def brier_score(confidences: Sequence[int], correct: Sequence[bool]) -> float:
    if len(confidences) != len(correct):
        raise ValueError("confidences and correct must have equal length")
    if not correct:
        return 0.0
    return sum(((c / 100.0) - float(y)) ** 2 for c, y in zip(confidences, correct)) / len(correct)


def expected_calibration_error(
    confidences: Sequence[int], correct: Sequence[bool], bins: int = 10
) -> tuple[float, list[dict]]:
    if len(confidences) != len(correct):
        raise ValueError("confidences and correct must have equal length")
    if bins < 1:
        raise ValueError("bins must be positive")
    n = len(correct)
    details: list[dict] = []
    if n == 0:
        return 0.0, details
    ece = 0.0
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        selected = [
            (c / 100.0, bool(y))
            for c, y in zip(confidences, correct)
            if ((low <= c / 100.0 <= high) if index == bins - 1 else (low <= c / 100.0 < high))
        ]
        if not selected:
            continue
        avg_conf = sum(x[0] for x in selected) / len(selected)
        avg_acc = sum(float(x[1]) for x in selected) / len(selected)
        weight = len(selected) / n
        ece += weight * abs(avg_conf - avg_acc)
        details.append({
            "bin_low": round(low, 3), "bin_high": round(high, 3),
            "count": len(selected), "accuracy": avg_acc,
            "average_confidence": avg_conf,
            "absolute_gap": abs(avg_conf - avg_acc),
        })
    return ece, details


def shannon_entropy(values: Iterable[int]) -> float:
    values = list(values)
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def normalized_entropy(values: Iterable[int]) -> float:
    values = list(values)
    distinct = len(set(values))
    if distinct <= 1:
        return 0.0
    return shannon_entropy(values) / math.log2(distinct)
