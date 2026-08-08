import json
from pathlib import Path
from demo import build_stats

ROOT=Path(__file__).resolve().parents[1]

def _result(provider,case_id,trial,answer,passed=True):
    return {"provider":provider,"model":"test-model","case_id":case_id,"trial":trial,"job_status":"EVALUATED","latency_ms":100+trial,"usage":{"total_tokens":100},"parsed_output":{"answer":answer,"confidence":90},"evaluation":{"passed":passed,"score":100 if passed else 0}}

def test_statistics_contract_has_surface_and_semantic_fields():
    case={"case_id":"C1","title":"Numeric","category":"test","evaluator":"numeric_exact"}
    stats=build_stats([_result("mock","C1",1,4),_result("mock","C1",2,"4.0")],["mock"],[case],2)
    row=stats["case_statistics"][0]
    required={"surface_consistency","semantic_consistency","surface_distinct_answers","semantic_distinct_answers","surface_entropy_bits","semantic_entropy_bits","surface_modal_answer","semantic_modal_answer"}
    assert required <= row.keys()
    assert row["surface_distinct_answers"]==2
    assert row["semantic_distinct_answers"]==1
    assert row["semantic_consistency"]==100.0

def test_dashboard_uses_v55_contract_names():
    html=(ROOT/"dashboard"/"index.html").read_text(encoding="utf-8")
    for field in ("surface_consistency","semantic_consistency","surface_distinct_answers","semantic_distinct_answers","surface_entropy_bits","semantic_entropy_bits","surface_modal_answer","semantic_modal_answer","mean_case_semantic_entropy_bits"):
        assert f"r.{field}" in html
    for stale in ("r.answer_consistency","r.distinct_answers","r.answer_entropy_bits","r.modal_answer"):
        assert stale not in html
