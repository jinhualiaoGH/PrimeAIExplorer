from __future__ import annotations

import argparse
import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from primeaiexplorer.cli import cmd_history, cmd_progress, cmd_resume


class WorkflowCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pilot = self.root / "pilot_002"
        (self.pilot / "text").mkdir(parents=True)
        self.dataset = self.root / "cases.csv"
        with self.dataset.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["case_id", "ground_truth", "window_size"])
            writer.writeheader()
            writer.writerow({"case_id": "CASE-W004-0002", "ground_truth": 6, "window_size": 4})
            writer.writerow({"case_id": "CASE-W008-0002", "ground_truth": 6, "window_size": 8})
        for case_id in ("CASE-W004-0002", "CASE-W008-0002"):
            (self.pilot / "text" / f"{case_id}.txt").write_text(f"Prompt for {case_id}", encoding="utf-8")
        (self.pilot / "responses.json").write_text(
            json.dumps([
                {
                    "case_id": "CASE-W004-0002",
                    "response": {"prediction": 4, "confidence": 18, "explanation": "A test."},
                },
                {"case_id": "CASE-W008-0002", "response": None},
            ]),
            encoding="utf-8",
        )
        self.args = argparse.Namespace(
            responses=str(self.pilot), dataset=str(self.dataset), prompts=None
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_progress_reports_window_counts(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_progress(self.args)
        text = out.getvalue()
        self.assertIn("Completed: 1 / 2", text)
        self.assertIn("W004:  1/1", text)
        self.assertIn("W008:  0/1", text)

    def test_history_lists_completed_case(self) -> None:
        args = argparse.Namespace(**vars(self.args), limit=0)
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_history(args)
        text = out.getvalue()
        self.assertIn("CASE-W004-0002", text)
        self.assertIn("Shown: 1 of 1", text)

    def test_resume_identifies_next_case(self) -> None:
        args = argparse.Namespace(**vars(self.args), open_editor=False)
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_resume(args)
        text = out.getvalue()
        self.assertIn("Next case: CASE-W008-0002", text)
        self.assertIn("current_response.json", text)
        self.assertIn("Prompt for CASE-W008-0002", text)


if __name__ == "__main__":
    unittest.main()
