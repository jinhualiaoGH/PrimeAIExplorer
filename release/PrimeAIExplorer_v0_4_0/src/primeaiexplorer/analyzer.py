from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime
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
    return {"unique_explanation_ratio": unique_ratio,"average_words": mean([len(TOKEN_RE.findall(x)) for x in explanations]) if explanations else 0.0,"top_content_words": [{"word": w, "count": n} for w, n in phrases],"reasoning_categories": dict(categories)}


def _cumulative_trends(records: list[ResponseRecord], bins: int) -> list[dict]:
    rows=[]
    for i in range(1,len(records)+1):
        part=records[:i]; conf=[r.confidence for r in part]; corr=[r.correct for r in part]
        ece,_=expected_calibration_error(conf,corr,bins=bins)
        rows.append({"n":i,"case_id":part[-1].case_id,"accuracy":exact_accuracy(corr),"brier":brier_score(conf,corr),"ece":ece,"entropy":shannon_entropy([r.prediction for r in part])})
    return rows


def _timing(records: list[ResponseRecord]) -> dict:
    durations=[r.response_seconds for r in records if r.response_seconds is not None and r.response_seconds >= 0]
    timestamps=[]
    for r in records:
        if r.collected_at:
            try: timestamps.append(datetime.fromisoformat(r.collected_at.replace('Z','+00:00')))
            except ValueError: pass
    timestamps.sort()
    intervals=[(b-a).total_seconds() for a,b in zip(timestamps,timestamps[1:]) if b>=a]
    return {"duration_count":len(durations),"mean_response_seconds":mean(durations) if durations else None,"median_response_seconds":median(durations) if durations else None,"timestamp_count":len(timestamps),"mean_collection_interval_seconds":mean(intervals) if intervals else None,"median_collection_interval_seconds":median(intervals) if intervals else None}


def analyze(records: list[ResponseRecord], bins: int = 10, dataset_case_count: int | None = None, ledger_entries: int | None = None, pending_entries: int = 0) -> dict:
    confidences=[r.confidence for r in records]; correct=[r.correct for r in records]; predictions=[r.prediction for r in records]; truths=[r.actual_gap for r in records]
    ece,calibration=expected_calibration_error(confidences,correct,bins=bins)
    by_window=defaultdict(list)
    for r in records: by_window[r.window].append(r)
    windows={}
    for window,rows in sorted(by_window.items(),key=lambda item:(-1 if item[0] is None else item[0])):
        windows[str(window)]={"count":len(rows),"accuracy":exact_accuracy([r.correct for r in rows]),"mean_confidence":mean(r.confidence for r in rows),"brier_score":brier_score([r.confidence for r in rows],[r.correct for r in rows])}
    pc=Counter(predictions); tc=Counter(truths); gaps=sorted(set(pc)|set(tc)); confusion=Counter((r.actual_gap,r.prediction) for r in records)
    coverage=(len(records)/dataset_case_count) if dataset_case_count else None
    return {"schema_version":"0.4.0","record_count":len(records),"ledger_entry_count":ledger_entries if ledger_entries is not None else len(records),"completed_entry_count":len(records),"pending_entry_count":pending_entries,"pilot_completion":(len(records)/ledger_entries) if ledger_entries else 0.0,"dataset_case_count":dataset_case_count,"dataset_coverage":coverage,"correct_count":sum(correct),"incorrect_count":len(records)-sum(correct),"accuracy":exact_accuracy(correct),"mean_confidence":mean(confidences) if confidences else 0.0,"median_confidence":median(confidences) if confidences else 0.0,"brier_score":brier_score(confidences,correct),"ece":ece,"prediction_entropy_bits":shannon_entropy(predictions),"normalized_prediction_entropy":normalized_entropy(predictions),"distinct_predictions":len(pc),"prediction_distribution":[{"prediction":k,"count":v} for k,v in sorted(pc.items())],"truth_distribution":[{"truth":k,"count":v} for k,v in sorted(tc.items())],"prediction_bias":[{"gap":g,"predicted":pc[g],"truth":tc[g],"bias":pc[g]-tc[g]} for g in gaps],"confusion_labels":gaps,"confusion_matrix":[{"truth":t,"prediction":p,"count":confusion[(t,p)]} for t in gaps for p in gaps if confusion[(t,p)]],"calibration_bins":calibration,"metric_trends":_cumulative_trends(records,bins),"timing":_timing(records),"by_window":windows,"explanations":explanation_profile([r.explanation for r in records]),"records":[asdict(r) for r in records]}
