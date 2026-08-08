
from demo import answer_entropy, normalized_entropy, percentile

def test_entropy_zero_for_stable_answers():
    assert answer_entropy(["4","4","4"]) == 0.0

def test_entropy_positive_for_mixed_answers():
    assert answer_entropy(["4","4","6"]) > 0.0

def test_normalized_entropy_bounded():
    h=normalized_entropy(["4","4","6"])
    assert 0.0 <= h <= 1.0

def test_percentile():
    assert percentile([1,2,3,4,5],0.95) == 4.8
