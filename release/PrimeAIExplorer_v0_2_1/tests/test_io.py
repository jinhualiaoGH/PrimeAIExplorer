from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from primeaiexplorer.io import load_dataset, load_records


class DatasetTests(unittest.TestCase):
    def test_load_canonical_dataset_and_response(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dataset = root / "cases.csv"
            with dataset.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["case_id", "pair_id", "window_size", "ground_truth"])
                writer.writerow(["CASE-W008-0002", "PAIR-0002", 8, 12])
            response_dir = root / "responses"
            response_dir.mkdir()
            (response_dir / "CASE-W008-0002.response.json").write_text(
                json.dumps({"prediction": 12, "confidence": 70, "explanation": "Local repetition."}),
                encoding="utf-8",
            )
            loaded = load_dataset(dataset)
            self.assertEqual(loaded["CASE-W008-0002"].ground_truth, 12)
            records = load_records(response_dir, dataset)
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0].correct)
            self.assertEqual(records[0].window, 8)


if __name__ == "__main__":
    unittest.main()
