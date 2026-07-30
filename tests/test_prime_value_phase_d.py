from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.prime_value_evaluation import (
    LeaderboardBuilder,
    PrimeValueEvaluationEngine,
    ResponseParser,
    stable_sha256,
)


def make_project(root: Path) -> dict:
    experiment_root = root / "experiments" / "EXP-000003"
    benchmark = experiment_root / "benchmark"
    public = benchmark / "cases" / "public"
    private = benchmark / "cases" / "private"
    public.mkdir(parents=True)
    private.mkdir(parents=True)

    cases = []
    targets = [11, 13, 17, 19]
    windows = [4, 4, 8, 8]
    for index, (target, window) in enumerate(zip(targets, windows), start=1):
        case_id = f"CASE-W{window:03d}-{index:06d}"
        public_case = {
            "case_id": case_id,
            "window_size": window,
            "observation": [2, 3, 5, 7],
        }
        private_case = {
            **public_case,
            "target": target,
            "answer_key_sha256": f"answer-{index}",
        }
        (public / f"{case_id}.json").write_text(
            json.dumps(public_case),
            encoding="utf-8",
        )
        (private / f"{case_id}.json").write_text(
            json.dumps(private_case),
            encoding="utf-8",
        )
        cases.append({
            "case_id": case_id,
            "window_size": window,
            "target_index_1_based": 100 + index,
            "public_case_sha256": f"public-{index}",
            "answer_key_sha256": f"answer-{index}",
            "prompt_sha256": f"prompt-{index}",
        })

    manifest = {
        "schema_version": "1.0",
        "experiment_id": "EXP-000003",
        "dataset_sha256": "dataset-hash",
        "total_case_count": len(cases),
        "cases": cases,
    }
    manifest["manifest_sha256"] = stable_sha256(manifest)
    (benchmark / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    return {
        "experiment": {"id": "EXP-000003"},
        "cases": {"output_root": "benchmark"},
    }


class PhaseDTests(unittest.TestCase):
    def test_response_parser_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "response.json"
            path.write_text(json.dumps({
                "prediction": 11,
                "confidence": 75,
                "explanation": "test",
                "latency_ms": 12.5,
            }), encoding="utf-8")
            parsed = ResponseParser().parse("CASE", path)
            self.assertTrue(parsed.schema_valid)
            self.assertEqual(parsed.prediction, 11)

    def test_response_parser_rejects_boolean_prediction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "response.json"
            path.write_text(json.dumps({
                "prediction": True,
                "confidence": 75,
                "explanation": "test",
            }), encoding="utf-8")
            parsed = ResponseParser().parse("CASE", path)
            self.assertFalse(parsed.schema_valid)

    def test_response_parser_rejects_confidence_range(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "response.json"
            path.write_text(json.dumps({
                "prediction": 11,
                "confidence": 101,
                "explanation": "test",
            }), encoding="utf-8")
            self.assertFalse(ResponseParser().parse("CASE", path).schema_valid)

    def test_prepare_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueEvaluationEngine(
                make_project(root),
                project_root=root,
            )
            result = engine.prepare_response_workspace("Model A")
            self.assertEqual(result["expected_case_count"], 4)
            self.assertEqual(len(list(engine.responses_root("Model A").glob("CASE-*.json"))), 4)

    def test_evaluation_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueEvaluationEngine(
                make_project(root),
                project_root=root,
            )
            engine.prepare_response_workspace("Model A")
            responses = engine.responses_root("Model A")
            predictions = [11, 12, 17, 23]
            for path, prediction in zip(sorted(responses.glob("CASE-*.json")), predictions):
                path.write_text(json.dumps({
                    "prediction": prediction,
                    "confidence": 50,
                    "explanation": "test",
                }), encoding="utf-8")
            summary = engine.evaluate("Model A")
            self.assertEqual(summary["overall"]["correct_count"], 2)
            self.assertAlmostEqual(summary["overall"]["exact_accuracy"], 0.5)
            self.assertEqual(summary["by_window"]["W004"]["case_count"], 2)

    def test_missing_response_is_scored_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueEvaluationEngine(
                make_project(root),
                project_root=root,
            )
            workspace = engine.responses_root("Model A")
            workspace.mkdir(parents=True)
            summary = engine.evaluate("Model A")
            self.assertEqual(summary["overall"]["response_exists_count"], 0)
            self.assertEqual(summary["overall"]["correct_count"], 0)

    def test_evaluation_overwrite_protection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = PrimeValueEvaluationEngine(
                make_project(root),
                project_root=root,
            )
            engine.responses_root("Model A").mkdir(parents=True)
            engine.evaluate("Model A")
            with self.assertRaises(FileExistsError):
                engine.evaluate("Model A")
            engine.evaluate("Model A", overwrite=True)

    def test_leaderboard_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evaluations = root / "evaluations"
            for slug, model, accuracy in [
                ("model-b", "Model B", 0.25),
                ("model-a", "Model A", 0.75),
            ]:
                path = evaluations / slug
                path.mkdir(parents=True)
                summary = {
                    "model_id": model,
                    "model_slug": slug,
                    "summary_sha256": slug,
                    "overall": {
                        "case_count": 4,
                        "correct_count": int(accuracy * 4),
                        "exact_accuracy": accuracy,
                        "valid_json_rate": 1.0,
                        "schema_valid_rate": 1.0,
                        "prime_valid_rate": 1.0,
                        "mean_absolute_error": 1.0,
                        "mean_confidence": 50.0,
                    },
                }
                (path / "summary.json").write_text(
                    json.dumps(summary),
                    encoding="utf-8",
                )
            leaderboard = LeaderboardBuilder(evaluations).build()
            self.assertEqual(leaderboard["entries"][0]["model_id"], "Model A")

    def test_deterministic_summary_hash(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            hashes = []
            for temporary in (first, second):
                root = Path(temporary)
                engine = PrimeValueEvaluationEngine(
                    make_project(root),
                    project_root=root,
                )
                engine.responses_root("Model A").mkdir(parents=True)
                hashes.append(engine.evaluate("Model A")["summary_sha256"])
            self.assertEqual(hashes[0], hashes[1])


if __name__ == "__main__":
    unittest.main()
