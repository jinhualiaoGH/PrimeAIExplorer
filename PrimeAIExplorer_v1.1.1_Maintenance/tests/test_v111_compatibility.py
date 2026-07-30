from __future__ import annotations

import unittest

from plugins.left_twin import is_prime_64, is_probable_prime_64


class LeftTwinCompatibilityTests(unittest.TestCase):
    def test_legacy_alias_is_available(self) -> None:
        self.assertIs(is_probable_prime_64, is_prime_64)

    def test_legacy_alias_matches_current_function(self) -> None:
        values = (1, 2, 3, 5, 9, 101, 103, 221)
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(
                    is_probable_prime_64(value),
                    is_prime_64(value),
                )


if __name__ == "__main__":
    unittest.main()
