
from evaluators import EvaluationEngine
E=EvaluationEngine()

def test_json_status_synonym():
    case={"evaluator":"json_semantic","expected_answer":{"service":"Atlas","records":1250,"seconds":3.8,"status":"completed successfully"}}
    r=E.evaluate(case,{"answer":{"service":"Atlas","records":1250,"seconds":3.8,"status":"success"}})
    assert r["passed"] and r["score"]==100

def test_sql_equivalent_query():
    case={"evaluator":"sql_semantic"}
    r=E.evaluate(case,{"answer":"SELECT customer_id, SUM(amount) AS total_amount FROM Sales GROUP BY customer_id HAVING SUM(amount) > 1000 ORDER BY total_amount DESC;"})
    assert r["passed"] and r["score"]==100

def test_sql_missing_having_fails():
    case={"evaluator":"sql_semantic"}
    r=E.evaluate(case,{"answer":"SELECT customer_id, SUM(amount) AS total_amount FROM Sales GROUP BY customer_id ORDER BY total_amount DESC;"})
    assert not r["passed"] and r["score"]<100

def test_time_12_hour_equivalence():
    r=E.evaluate({"evaluator":"time_exact","expected_answer":"10:10"},{"answer":"10:10 AM"})
    assert r["passed"]

def test_numeric_string_equivalence():
    r=E.evaluate({"evaluator":"numeric_exact","expected_answer":4},{"answer":"4"})
    assert r["passed"]
