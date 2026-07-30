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
        rows.append({"n":i,"case_id":part[-1].case_id,"accuracy":exact_accuracy(corr),"brier":brier_score(conf,corr),"ece":ece,"entropy":shannon_entropy([r.prediction for r in part]),"mean_absolute_error":mean(abs(r.prediction-r.actual_gap) for r in part),"mean_signed_error":mean(r.prediction-r.actual_gap for r in part)})
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


def _family(gap: int) -> str:
    if gap == 2: return "twin"
    if gap <= 8: return "small"
    if gap <= 14: return "medium"
    return "large"


def _confidence_histogram(records: list[ResponseRecord]) -> list[dict]:
    rows=[]
    for low in range(0,100,10):
        high=low+10
        selected=[r for r in records if (low <= r.confidence <= high if high==100 else low <= r.confidence < high)]
        rows.append({"bin_low":low,"bin_high":high,"count":len(selected),"accuracy":exact_accuracy([r.correct for r in selected]) if selected else 0.0,"mean_absolute_error":mean(abs(r.prediction-r.actual_gap) for r in selected) if selected else 0.0})
    return rows


def analyze(records: list[ResponseRecord], bins: int = 10, dataset_case_count: int | None = None, ledger_entries: int | None = None, pending_entries: int = 0) -> dict:
    confidences=[r.confidence for r in records]; correct=[r.correct for r in records]; predictions=[r.prediction for r in records]; truths=[r.actual_gap for r in records]
    signed_errors=[r.prediction-r.actual_gap for r in records]; absolute_errors=[abs(x) for x in signed_errors]
    ece,calibration=expected_calibration_error(confidences,correct,bins=bins)
    by_window=defaultdict(list)
    for r in records: by_window[r.window].append(r)
    windows={}; window_rows=[]
    for window,rows in sorted(by_window.items(),key=lambda item:(-1 if item[0] is None else item[0])):
        data={"window":window,"count":len(rows),"accuracy":exact_accuracy([r.correct for r in rows]),"mean_confidence":mean(r.confidence for r in rows),"brier_score":brier_score([r.confidence for r in rows],[r.correct for r in rows]),"prediction_entropy_bits":shannon_entropy([r.prediction for r in rows]),"mean_signed_error":mean(r.prediction-r.actual_gap for r in rows),"mean_absolute_error":mean(abs(r.prediction-r.actual_gap) for r in rows)}
        windows[str(window)]=dict(data); window_rows.append(data)
    pc=Counter(predictions); tc=Counter(truths); gaps=sorted(set(pc)|set(tc)); confusion=Counter((r.actual_gap,r.prediction) for r in records)
    transitions=Counter((a.prediction,b.prediction) for a,b in zip(records,records[1:])); transition_labels=sorted(set(predictions)); error_counts=Counter(signed_errors)
    family_rows=[]
    for family in ("twin","small","medium","large"):
        selected=[r for r in records if _family(r.actual_gap)==family]
        family_rows.append({"family":family,"count":len(selected),"accuracy":exact_accuracy([r.correct for r in selected]) if selected else 0.0,"mean_confidence":mean(r.confidence for r in selected) if selected else 0.0,"mean_absolute_error":mean(abs(r.prediction-r.actual_gap) for r in selected) if selected else 0.0,"predicted_in_family":sum(1 for r in records if _family(r.prediction)==family),"truth_in_family":len(selected)})
    timeline=[{"n":i,"case_id":r.case_id,"window":r.window,"prediction":r.prediction,"truth":r.actual_gap,"confidence":r.confidence,"correct":r.correct,"signed_error":r.prediction-r.actual_gap,"absolute_error":abs(r.prediction-r.actual_gap)} for i,r in enumerate(records,1)]
    coverage=(len(records)/dataset_case_count) if dataset_case_count else None
    return {"schema_version":"0.5.0","record_count":len(records),"ledger_entry_count":ledger_entries if ledger_entries is not None else len(records),"completed_entry_count":len(records),"pending_entry_count":pending_entries,"pilot_completion":(len(records)/ledger_entries) if ledger_entries else 0.0,"dataset_case_count":dataset_case_count,"dataset_coverage":coverage,"correct_count":sum(correct),"incorrect_count":len(records)-sum(correct),"accuracy":exact_accuracy(correct),"mean_confidence":mean(confidences) if confidences else 0.0,"median_confidence":median(confidences) if confidences else 0.0,"brier_score":brier_score(confidences,correct),"ece":ece,"prediction_entropy_bits":shannon_entropy(predictions),"normalized_prediction_entropy":normalized_entropy(predictions),"distinct_predictions":len(pc),"mean_signed_error":mean(signed_errors) if signed_errors else 0.0,"mean_absolute_error":mean(absolute_errors) if absolute_errors else 0.0,"median_absolute_error":median(absolute_errors) if absolute_errors else 0.0,"exact_error_rate":sum(1 for x in signed_errors if x==0)/len(signed_errors) if signed_errors else 0.0,"prediction_distribution":[{"prediction":k,"count":v,"frequency":v/len(records),"rank":rank+1} for rank,(k,v) in enumerate(sorted(pc.items(),key=lambda x:(-x[1],x[0])))],"truth_distribution":[{"truth":k,"count":v,"frequency":v/len(records),"rank":rank+1} for rank,(k,v) in enumerate(sorted(tc.items(),key=lambda x:(-x[1],x[0])))],"gap_spectrum":[{"gap":g,"predicted":pc[g],"truth":tc[g],"bias":pc[g]-tc[g],"predicted_frequency":pc[g]/len(records),"truth_frequency":tc[g]/len(records),"absolute_bias":abs(pc[g]-tc[g])} for g in gaps],"prediction_bias":[{"gap":g,"predicted":pc[g],"truth":tc[g],"bias":pc[g]-tc[g]} for g in gaps],"confusion_labels":gaps,"confusion_matrix":[{"truth":t,"prediction":p,"count":confusion[(t,p)]} for t in gaps for p in gaps if confusion[(t,p)]],"transition_labels":transition_labels,"prediction_transitions":[{"from_prediction":a,"to_prediction":b,"count":transitions[(a,b)]} for a in transition_labels for b in transition_labels if transitions[(a,b)]],"error_distribution":[{"signed_error":e,"count":c,"frequency":c/len(records)} for e,c in sorted(error_counts.items())],"confidence_histogram":_confidence_histogram(records),"confidence_error":[{"case_id":r.case_id,"confidence":r.confidence,"absolute_error":abs(r.prediction-r.actual_gap),"signed_error":r.prediction-r.actual_gap,"correct":r.correct} for r in records],"gap_families":family_rows,"timeline":timeline,"calibration_bins":calibration,"metric_trends":_cumulative_trends(records,bins),"timing":_timing(records),"window_observatory":window_rows,"by_window":windows,"explanations":explanation_profile([r.explanation for r in records]),"records":[asdict(r) for r in records]}
