from __future__ import annotations
import unittest
from primeaiexplorer.analyzer import analyze
from primeaiexplorer.io import ResponseRecord

class BehaviorObservatoryTests(unittest.TestCase):
    def records(self):
        return [ResponseRecord(case_id=f"CASE-W004-000{i}",window=4,prediction=p,confidence=c,explanation="test",actual_gap=t,response_path="x",collection_sha256="a",entry_sha256=str(i),response_sha256=str(i),correct=p==t) for i,(p,t,c) in enumerate([(6,12,20),(6,6,80),(4,12,90),(4,4,70)],1)]
    def test_persistence(self):
        s=analyze(self.records())
        self.assertEqual(s["persistence"]["switch_count"],1)
        self.assertEqual(s["persistence"]["max_run_length"],2)
    def test_surprise_ranking(self):
        s=analyze(self.records())
        self.assertEqual(len(s["surprise_index"]),4)
        self.assertEqual(s["surprise_index"][0]["rank"],1)
    def test_fingerprint(self):
        metrics={x["metric"] for x in analyze(self.records())["model_fingerprint"]}
        self.assertIn("switch_rate",metrics)
        self.assertIn("favorite_prediction",metrics)

if __name__ == "__main__": unittest.main()
