from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict
from statistics import mean, median

from .io import ResponseRecord
from .metrics import brier_score, exact_accuracy, expected_calibration_error, normalized_entropy, shannon_entropy

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]+")
STOP = {"the","a","an","is","are","to","of","in","and","this","that","it","for","as","with","be","next"}


def explanation_profile(explanations: list[str]) -> dict:
    tokens = [t.lower() for text in explanations for t in TOKEN_RE.findall(text)]
    filtered = [t for t in tokens if t not in STOP]
    phrases = Counter(filtered).most_common(15)
    unique_ratio = len(set(explanations)) / len(explanations) if explanations else 0.0
    categories = Counter()
    for text in explanations:
        low = text.lower()
        if any(k in low for k in ("repeat", "pattern", "sequence", "continu")): categories["pattern_continuation"] += 1
        if any(k in low for k in ("frequent", "common", "typical", "mode", "likely")): categories["frequency_prior"] += 1
        if any(k in low for k in ("random", "uncertain", "unpredict", "limited")): categories["uncertainty"] += 1
        if any(k in low for k in ("trend", "increase", "decrease")): categories["trend"] += 1
        if any(k in low for k in ("recent", "local", "last", "nearby")): categories["local_context"] += 1
    return {
        "unique_explanation_ratio": unique_ratio,
        "average_words": mean([len(TOKEN_RE.findall(x)) for x in explanations]) if explanations else 0.0,
        "top_content_words": [{"word": w, "count": n} for w, n in phrases],
        "reasoning_categories": dict(categories),
    }


def analyze(records: list[ResponseRecord], bins: int = 10, dataset_case_count: int | None = None) -> dict:
    confidences = [r.confidence for r in records]
    correct = [r.correct for r in records]
    predictions = [r.prediction for r in records]
    ece, calibration = expected_calibration_error(confidences, correct, bins=bins)
    by_window = defaultdict(list)
    for record in records:
        by_window[record.window].append(record)
    windows = {}
    for window, rows in sorted(by_window.items(), key=lambda item: (-1 if item[0] is None else item[0])):
        windows[str(window)] = {
            "count": len(rows),
            "accuracy": exact_accuracy([r.correct for r in rows]),
            "mean_confidence": mean(r.confidence for r in rows),
            "brier_score": brier_score([r.confidence for r in rows], [r.correct for r in rows]),
        }
    prediction_counts = Counter(predictions)
    coverage = (len(records) / dataset_case_count) if dataset_case_count else None
    return {
        "schema_version": "0.2.3",
        "record_count": len(records),
        "dataset_case_count": dataset_case_count,
        "dataset_coverage": coverage,
        "correct_count": sum(correct),
        "incorrect_count": len(records) - sum(correct),
        "accuracy": exact_accuracy(correct),
        "mean_confidence": mean(confidences) if confidences else 0.0,
        "median_confidence": median(confidences) if confidences else 0.0,
        "brier_score": brier_score(confidences, correct),
        "ece": ece,
        "prediction_entropy_bits": shannon_entropy(predictions),
        "normalized_prediction_entropy": normalized_entropy(predictions),
        "distinct_predictions": len(prediction_counts),
        "prediction_distribution": [{"prediction": k, "count": v} for k, v in sorted(prediction_counts.items())],
        "calibration_bins": calibration,
        "by_window": windows,
        "explanations": explanation_profile([r.explanation for r in records]),
        "records": [asdict(r) for r in records],
    }
