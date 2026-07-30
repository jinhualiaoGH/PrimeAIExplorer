from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from primeaiexplorer.io import commit_pilot_response, inspect_ledger_status


class CollectionAssistantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pilot = self.root / "pilot_002"
        self.pilot.mkdir()
        (self.pilot / "text").mkdir()
        self.dataset = self.root / "cases.csv"
        with self.dataset.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["case_id", "ground_truth", "window_size"])
            writer.writeheader()
            writer.writerow({"case_id": "CASE-W004-0002", "ground_truth": 6, "window_size": 4})
            writer.writerow({"case_id": "CASE-W008-0002", "ground_truth": 6, "window_size": 8})
        for case_id in ("CASE-W004-0002", "CASE-W008-0002"):
            (self.pilot / "text" / f"{case_id}.txt").write_text(case_id, encoding="utf-8")
        self.ledger = self.pilot / "responses.json"
        self.ledger.write_text(
            json.dumps([
                {"case_id": "CASE-W004-0002", "response": None},
                {"case_id": "CASE-W008-0002", "response": None},
            ]),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_commit_next_response_creates_backup(self) -> None:
        case_id, ledger, backup = commit_pilot_response(
            self.pilot,
            self.dataset,
            {"prediction": 4, "confidence": 18, "explanation": "A test."},
            model="GPT-5.6 Thinking",
        )
        self.assertEqual(case_id, "CASE-W004-0002")
        self.assertEqual(ledger, self.ledger.resolve())
        self.assertIsNotNone(backup)
        self.assertTrue(backup and backup.is_file())
        document = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(document[0]["response"]["prediction"], 4)
        self.assertIsNone(document[1]["response"])
        status = inspect_ledger_status(self.pilot)
        self.assertEqual(status.completed_entries, 1)
        self.assertEqual(status.pending_entries, 1)

    def test_existing_response_is_not_overwritten(self) -> None:
        commit_pilot_response(
            self.pilot,
            self.dataset,
            {"prediction": 4, "confidence": 18, "explanation": "A test."},
            case_id="CASE-W004-0002",
        )
        with self.assertRaisesRegex(ValueError, "already has a committed response"):
            commit_pilot_response(
                self.pilot,
                self.dataset,
                {"prediction": 6, "confidence": 90, "explanation": "Replacement."},
                case_id="CASE-W004-0002",
            )

    def test_dry_run_does_not_change_ledger(self) -> None:
        before = self.ledger.read_bytes()
        case_id, _, backup = commit_pilot_response(
            self.pilot,
            self.dataset,
            {"prediction": 4, "confidence": 18, "explanation": "A test."},
            dry_run=True,
        )
        self.assertEqual(case_id, "CASE-W004-0002")
        self.assertIsNone(backup)
        self.assertEqual(before, self.ledger.read_bytes())


if __name__ == "__main__":
    unittest.main()
