from __future__ import annotations
import unittest
from primeaiexplorer.analyzer import analyze
from primeaiexplorer.io import ResponseRecord


def rec(case,pred,truth,conf,stamp=None,seconds=None):
    return ResponseRecord(case_id=case,window=4,prediction=pred,confidence=conf,explanation='common pattern',actual_gap=truth,response_path='x',collection_sha256='c',entry_sha256=case,response_sha256=case,correct=pred==truth,collected_at=stamp,response_seconds=seconds)

class ObservatoryAnalyticsTests(unittest.TestCase):
    def test_bias_confusion_and_trends(self):
        summary=analyze([rec('CASE-W004-0001',6,12,20),rec('CASE-W004-0002',6,6,80)],dataset_case_count=2,ledger_entries=2)
        bias={r['gap']:r for r in summary['prediction_bias']}
        self.assertEqual(bias[6]['bias'],1)
        self.assertIn({'truth':12,'prediction':6,'count':1},summary['confusion_matrix'])
        self.assertEqual(len(summary['metric_trends']),2)
    def test_timing_statistics(self):
        summary=analyze([rec('CASE-W004-0001',6,6,80,'2026-01-01T00:00:00Z',10),rec('CASE-W004-0002',8,8,80,'2026-01-01T00:01:00Z',20)],ledger_entries=2)
        self.assertEqual(summary['timing']['mean_response_seconds'],15)
        self.assertEqual(summary['timing']['mean_collection_interval_seconds'],60)

if __name__=='__main__': unittest.main()
