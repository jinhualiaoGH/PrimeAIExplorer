import json
import tempfile
import unittest
from pathlib import Path

from primeaiexplorer.io import load_records


class AggregateResponseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.dataset = self.root / "cases.csv"
        self.dataset.write_text(
            "case_id,pair_id,window_size,ground_truth\n"
            "CASE-W004-0001,PAIR-0001,4,6\n"
            "CASE-W008-0001,PAIR-0001,8,6\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_list_under_responses(self):
        path = self.root / "responses.json"
        path.write_text(json.dumps({"responses": [
            {"case_id": "CASE-W004-0001", "prediction": 6, "confidence": 80, "explanation": "Common local pattern."},
            {"case_id": "CASE-W008-0001", "response": {"prediction": 4, "confidence": 60, "explanation": "Uncertain continuation."}},
        ]}), encoding="utf-8")
        records = load_records(path, self.dataset)
        self.assertEqual(len(records), 2)
        self.assertTrue(records[0].correct)
        self.assertFalse(records[1].correct)

    def test_case_keyed_mapping(self):
        folder = self.root / "pilot"
        folder.mkdir()
        path = folder / "responses.json"
        path.write_text(json.dumps({
            "CASE-W004-0001": {"prediction": 6, "confidence": 90, "explanation": "Pattern repetition."},
            "CASE-W008-0001": {"prediction": 6, "confidence": 75, "explanation": "Typical small gap."},
        }), encoding="utf-8")
        records = load_records(folder, self.dataset)
        self.assertEqual(len(records), 2)
        self.assertTrue(all(record.correct for record in records))

    def test_embedded_json_string(self):
        path = self.root / "responses.json"
        path.write_text(json.dumps({"responses": [
            {"case_id": "CASE-W004-0001", "response": '{"prediction":6,"confidence":70,"explanation":"Frequency prior."}'},
        ]}), encoding="utf-8")
        records = load_records(path, self.dataset)
        self.assertEqual(records[0].prediction, 6)


if __name__ == "__main__":
    unittest.main()
