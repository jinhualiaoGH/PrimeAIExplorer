from __future__ import annotations

import unittest

from primeaiexplorer.metrics import (
    brier_score,
    exact_accuracy,
    expected_calibration_error,
    normalized_entropy,
    shannon_entropy,
)


class MetricsTests(unittest.TestCase):
    def test_accuracy(self) -> None:
        self.assertEqual(exact_accuracy([True, False, True]), 2 / 3)

    def test_brier(self) -> None:
        self.assertAlmostEqual(brier_score([100, 0], [True, False]), 0.0)

    def test_ece(self) -> None:
        ece, _ = expected_calibration_error([100, 0], [True, False])
        self.assertAlmostEqual(ece, 0.0)

    def test_entropy(self) -> None:
        self.assertEqual(shannon_entropy([6, 6, 6]), 0.0)
        self.assertEqual(normalized_entropy([6, 6, 6]), 0.0)
        self.assertFalse(str(shannon_entropy([6, 6, 6])).startswith("-"))


if __name__ == "__main__":
    unittest.main()
