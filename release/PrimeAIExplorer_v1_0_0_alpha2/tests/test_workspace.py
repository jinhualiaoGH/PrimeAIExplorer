from __future__ import annotations

import argparse
import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from primeaiexplorer.cli import cmd_workspace


class InteractiveWorkspaceTests(unittest.TestCase):
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
            (self.pilot / "text" / f"{case_id}.txt").write_text(
                f"Prompt for {case_id}", encoding="utf-8"
            )
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
        (self.pilot / "current_response.json").write_text(
            json.dumps({"prediction": 6, "confidence": 60, "explanation": "Valid."}),
            encoding="utf-8",
        )
        self.output = self.root / "analysis_v031"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def args(self, commands: str) -> argparse.Namespace:
        return argparse.Namespace(
            responses=str(self.pilot),
            dataset=str(self.dataset),
            prompts=None,
            model="GPT-5.6 Thinking",
            experiment_id="EXP-TEST",
            pilot_id="pilot_002",
            analysis_output=str(self.output),
            collection_mode="manual_chat",
            bins=10,
            history_limit=10,
            auto_refresh=True,
            commands=commands,
        )

    def test_scripted_workspace_progress_prompt_and_exit(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_workspace(self.args("progress,prompt,exit"))
        text = out.getvalue()
        self.assertIn("Interactive Workspace", text)
        self.assertIn("Completed: 1 / 2", text)
        self.assertIn("CASE-W008-0002", text)
        self.assertIn("Workspace closed", text)

    def test_workspace_commit_refreshes_analysis(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_workspace(self.args("validate,commit,history,exit"))
        text = out.getvalue()
        self.assertIn("validated (dry run)", text)
        self.assertIn("Response: committed", text)
        self.assertIn("Analysis refreshed", text)
        self.assertTrue((self.output / "report.html").is_file())
        document = json.loads((self.pilot / "responses.json").read_text(encoding="utf-8"))
        self.assertIsNotNone(document[1]["response"])

    def test_workspace_unknown_command_warns(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_workspace(self.args("banana,exit"))
        self.assertIn("Unknown selection", out.getvalue())

    def test_workspace_accepts_numeric_trailing_parenthesis(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            cmd_workspace(self.args("4),exit"))
        self.assertIn("validated (dry run)", out.getvalue())

class WorkspaceSelectionNormalizationTests(unittest.TestCase):
    def test_numeric_punctuation_variants(self) -> None:
        from primeaiexplorer.cli import _normalize_workspace_selection
        for value in ("4", "4)", "4.", "(4)", "[4]", " 4: "):
            with self.subTest(value=value):
                self.assertEqual(_normalize_workspace_selection(value), "4")

    def test_named_commands_are_case_insensitive(self) -> None:
        from primeaiexplorer.cli import _normalize_workspace_selection
        self.assertEqual(_normalize_workspace_selection(" Validate "), "validate")
        self.assertEqual(_normalize_workspace_selection("COMMIT"), "commit")

if __name__ == "__main__":
    unittest.main()
