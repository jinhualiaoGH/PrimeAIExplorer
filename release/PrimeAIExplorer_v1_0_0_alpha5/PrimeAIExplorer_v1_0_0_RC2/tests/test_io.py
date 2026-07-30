from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from primeaiexplorer.io import inspect_ledger_status, load_records, parse_json_documents


class NativeResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dataset = self.root / "cases.csv"
        self.dataset.write_text(
            "case_id,ground_truth,window_size,pair_id\n"
            "CASE-W004-0001,6,4,PAIR-0001\n"
            "CASE-W008-0001,6,8,PAIR-0001\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _make_prompts(self) -> Path:
        pilot = self.root / "pilot"
        pilot.mkdir()
        (pilot / "CASE-W004-0001.txt").write_text("prompt", encoding="utf-8")
        (pilot / "CASE-W008-0001.txt").write_text("prompt", encoding="utf-8")
        return pilot

    def test_bom_concatenated_objects_without_case_ids(self) -> None:
        pilot = self._make_prompts()
        payload = (
            '\ufeff{"prediction":6,"confidence":18,"explanation":"common gap"}\n\n'
            '{"prediction":6,"confidence":100,"explanation":"exact sequence"}\n'
        )
        (pilot / "responses.json").write_text(payload, encoding="utf-8")
        records = load_records(pilot, self.dataset)
        self.assertEqual([r.case_id for r in records], ["CASE-W004-0001", "CASE-W008-0001"])
        self.assertEqual(len({r.collection_sha256 for r in records}), 1)
        self.assertEqual(len({r.entry_sha256 for r in records}), 2)
        self.assertTrue(all(r.response_sha256 == r.entry_sha256 for r in records))

    def test_standard_aggregate_with_case_ids(self) -> None:
        pilot = self._make_prompts()
        data = {"responses": [
            {"case_id": "CASE-W004-0001", "prediction": 6, "confidence": 50, "explanation": "x"},
            {"case_id": "CASE-W008-0001", "prediction": 6, "confidence": 60, "explanation": "y"},
        ]}
        (pilot / "responses.json").write_text(json.dumps(data), encoding="utf-8")
        records = load_records(pilot, self.dataset)
        self.assertEqual(len(records), 2)

    def test_ndjson(self) -> None:
        path = self.root / "responses.json"
        path.write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
        self.assertEqual(parse_json_documents(path), [{"a": 1}, {"b": 2}])

    def test_nested_text_prompt_directory(self) -> None:
        pilot = self.root / "pilot_nested"
        text = pilot / "text"
        text.mkdir(parents=True)
        (text / "CASE-W004-0001.txt").write_text("prompt", encoding="utf-8")
        (text / "CASE-W008-0001.txt").write_text("prompt", encoding="utf-8")
        (pilot / "responses.json").write_text(
            '{"prediction":6,"confidence":10,"explanation":"a"}\n'
            '{"prediction":6,"confidence":20,"explanation":"b"}\n',
            encoding="utf-8",
        )
        records = load_records(pilot, self.dataset)
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()

class PartialLedgerTests(unittest.TestCase):
    def test_pending_null_entries_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "cases.csv"
            dataset.write_text(
                "case_id,ground_truth,window_size,pair_id\n"
                "CASE-W004-0002,6,4,PAIR-0002\n"
                "CASE-W008-0002,6,8,PAIR-0002\n",
                encoding="utf-8",
            )
            pilot = root / "pilot"
            pilot.mkdir()
            (pilot / "responses.json").write_text(json.dumps([
                {"case_id":"CASE-W004-0002","response":{"prediction":4,"confidence":18,"explanation":"short guess"}},
                {"case_id":"CASE-W008-0002","response":None},
            ]), encoding="utf-8")
            records = load_records(pilot, dataset)
            status = inspect_ledger_status(pilot)
            self.assertEqual(len(records), 1)
            self.assertEqual(status.ledger_entries, 2)
            self.assertEqual(status.pending_entries, 1)
