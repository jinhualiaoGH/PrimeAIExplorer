from __future__ import annotations

import unittest

from plugins.left_twin import is_probable_prime_64


class LeftTwinPrimalityTests(unittest.TestCase):
    def test_small_primes(self) -> None:
        self.assertTrue(is_probable_prime_64(3))
        self.assertTrue(is_probable_prime_64(5))
        self.assertTrue(is_probable_prime_64(11))

    def test_composites(self) -> None:
        self.assertFalse(is_probable_prime_64(1))
        self.assertFalse(is_probable_prime_64(9))
        self.assertFalse(is_probable_prime_64(21))

    def test_left_twin(self) -> None:
        self.assertTrue(is_probable_prime_64(59))
        self.assertTrue(is_probable_prime_64(61))


if __name__ == "__main__":
    unittest.main()
