from demo import canonicalize_answer, latency_tail_ratio

def test_numeric(): assert canonicalize_answer({"evaluator":"numeric_exact"},4)==canonicalize_answer({"evaluator":"numeric_exact"},"4.0")
def test_time(): assert canonicalize_answer({"evaluator":"time_exact"},"10:10")==canonicalize_answer({"evaluator":"time_exact"},"10:10 AM")
def test_tail(): assert latency_tail_ratio(100,20)==5.0
