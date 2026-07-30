from __future__ import annotations
import unittest
from primeaiexplorer.analyzer import analyze
from primeaiexplorer.io import ResponseRecord

def rec(case,window,pred,truth,conf):
    return ResponseRecord(case_id=case,window=window,prediction=pred,confidence=conf,explanation="common pattern",actual_gap=truth,response_path="x",collection_sha256="c",entry_sha256=case,response_sha256=case,correct=pred==truth)

class ScientificObservatoryTests(unittest.TestCase):
    def setUp(self):
        self.summary=analyze([rec("CASE-W004-0001",4,6,12,20),rec("CASE-W008-0001",8,6,6,80),rec("CASE-W016-0001",16,4,12,30)],dataset_case_count=3,ledger_entries=3)
    def test_error_and_spectrum(self):
        self.assertAlmostEqual(self.summary["mean_signed_error"],-14/3)
        self.assertEqual(sum(r["count"] for r in self.summary["error_distribution"]),3)
        self.assertTrue(any(r["gap"]==6 for r in self.summary["gap_spectrum"]))
    def test_transitions_and_families(self):
        self.assertEqual(sum(r["count"] for r in self.summary["prediction_transitions"]),2)
        self.assertEqual(sum(r["truth_in_family"] for r in self.summary["gap_families"]),3)
    def test_confidence_and_window(self):
        self.assertEqual(sum(r["count"] for r in self.summary["confidence_histogram"]),3)
        self.assertEqual(len(self.summary["window_observatory"]),3)
        self.assertEqual(len(self.summary["confidence_error"]),3)

if __name__=="__main__": unittest.main()
