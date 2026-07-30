import unittest
from primeaiexplorer.metrics import brier_score, exact_accuracy, expected_calibration_error, shannon_entropy
class MetricsTests(unittest.TestCase):
 def test_accuracy(self): self.assertEqual(exact_accuracy([True,False,True]),2/3)
 def test_brier(self): self.assertAlmostEqual(brier_score([100,0],[True,False]),0.0)
 def test_entropy(self): self.assertAlmostEqual(shannon_entropy([2,2,2]),0.0)
 def test_ece(self):
  ece,_=expected_calibration_error([100,0],[True,False]);self.assertAlmostEqual(ece,0.0)
if __name__=="__main__":unittest.main()
