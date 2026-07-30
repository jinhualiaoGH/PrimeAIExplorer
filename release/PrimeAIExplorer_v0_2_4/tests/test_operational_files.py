from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from primeaiexplorer.io import discover_response_sources


class OperationalFileIgnoreTests(unittest.TestCase):
    def test_current_response_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            (root / "responses.json").write_text(
                json.dumps(
                    [
                        {
                            "case_id": "CASE-W004-0001",
                            "response": {
                                "prediction": 6,
                                "confidence": 50,
                                "explanation": "Test response.",
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )

            (root / "current_response.json").write_text(
                json.dumps(
                    {
                        "prediction": 8,
                        "confidence": 20,
                        "explanation": "Uncommitted working response.",
                    }
                ),
                encoding="utf-8",
            )

            (root / "pilot_manifest.json").write_text(
                json.dumps({"pilot_id": "pilot_001"}),
                encoding="utf-8",
            )

            aggregates, individuals = discover_response_sources(root)

            self.assertEqual(
                [path.name for path in aggregates],
                ["responses.json"],
            )

            self.assertEqual(
                individuals,
                [],
            )


if __name__ == "__main__":
    unittest.main()
