from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Mapping
import csv
import io
import json
import math
import os
import tempfile

from plugins.left_twin import is_prime_64


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        temp_path.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
    )


def slugify_model_id(model_id: str) -> str:
    cleaned = []
    previous_dash = False
    for character in model_id.strip():
        if character.isalnum():
            cleaned.append(character.lower())
            previous_dash = False
        elif not previous_dash:
            cleaned.append("-")
            previous_dash = True
    slug = "".join(cleaned).strip("-")
    if not slug:
        raise ValueError("model_id must contain at least one alphanumeric character.")
    return slug


@dataclass(frozen=True)
class ParsedResponse:
    case_id: str
    source_path: Path
    response_exists: bool
    valid_json: bool
    schema_valid: bool
    prediction: int | None
    confidence: int | None
    explanation: str | None
    latency_ms: float | None
    parse_error: str | None
    response_sha256: str | None


class ResponseParser:
    required_fields = ("prediction", "confidence", "explanation")

    @staticmethod
    def _is_integer(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    def parse(self, case_id: str, path: Path) -> ParsedResponse:
        if not path.exists():
            return ParsedResponse(
                case_id=case_id,
                source_path=path,
                response_exists=False,
                valid_json=False,
                schema_valid=False,
                prediction=None,
                confidence=None,
                explanation=None,
                latency_ms=None,
                parse_error="response file missing",
                response_sha256=None,
            )

        raw = path.read_bytes()
        digest = sha256(raw).hexdigest()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            return ParsedResponse(
                case_id=case_id,
                source_path=path,
                response_exists=True,
                valid_json=False,
                schema_valid=False,
                prediction=None,
                confidence=None,
                explanation=None,
                latency_ms=None,
                parse_error=f"invalid JSON: {exc}",
                response_sha256=digest,
            )

        if not isinstance(payload, dict):
            return ParsedResponse(
                case_id=case_id,
                source_path=path,
                response_exists=True,
                valid_json=True,
                schema_valid=False,
                prediction=None,
                confidence=None,
                explanation=None,
                latency_ms=None,
                parse_error="response must be a JSON object",
                response_sha256=digest,
            )

        missing = [field for field in self.required_fields if field not in payload]
        prediction = payload.get("prediction")
        confidence = payload.get("confidence")
        explanation = payload.get("explanation")
        latency = payload.get("latency_ms")

        errors: list[str] = []
        if missing:
            errors.append("missing fields: " + ", ".join(missing))
        if not self._is_integer(prediction):
            errors.append("prediction must be an integer")
        if not self._is_integer(confidence) or not 0 <= confidence <= 100:
            errors.append("confidence must be an integer from 0 to 100")
        if not isinstance(explanation, str):
            errors.append("explanation must be text")
        if latency is not None:
            if isinstance(latency, bool) or not isinstance(latency, (int, float)):
                errors.append("latency_ms must be numeric")
            elif not math.isfinite(float(latency)) or float(latency) < 0:
                errors.append("latency_ms must be finite and nonnegative")

        return ParsedResponse(
            case_id=case_id,
            source_path=path,
            response_exists=True,
            valid_json=True,
            schema_valid=not errors,
            prediction=int(prediction) if self._is_integer(prediction) else None,
            confidence=int(confidence) if self._is_integer(confidence) else None,
            explanation=explanation if isinstance(explanation, str) else None,
            latency_ms=float(latency) if latency is not None and isinstance(latency, (int, float)) and not isinstance(latency, bool) and math.isfinite(float(latency)) and float(latency) >= 0 else None,
            parse_error="; ".join(errors) if errors else None,
            response_sha256=digest,
        )


class PrimeValueEvaluationEngine:
    schema_version = "1.0"
    engine_version = "1.3.0"

    def __init__(self, config: Mapping[str, Any], *, project_root: Path) -> None:
        self.config = dict(config)
        self.project_root = project_root.resolve()
        self.experiment_id = self.config["experiment"]["id"]
        self.parser = ResponseParser()

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path.resolve() if path.is_absolute() else (self.project_root / path).resolve()

    @property
    def benchmark_root(self) -> Path:
        output = self.config["cases"].get("output_root", "benchmark")
        return self._resolve(f"experiments/{self.experiment_id}/{output}")

    @property
    def benchmark_manifest_path(self) -> Path:
        return self.benchmark_root / "manifest.json"

    def responses_root(self, model_id: str) -> Path:
        return self._resolve(
            f"experiments/{self.experiment_id}/responses/{slugify_model_id(model_id)}"
        )

    def evaluation_root(self, model_id: str) -> Path:
        return self._resolve(
            f"experiments/{self.experiment_id}/evaluations/{slugify_model_id(model_id)}"
        )

    def _load_manifest(self) -> dict[str, Any]:
        if not self.benchmark_manifest_path.exists():
            raise FileNotFoundError(
                f"Benchmark manifest does not exist: {self.benchmark_manifest_path}"
            )
        manifest = json.loads(
            self.benchmark_manifest_path.read_text(encoding="utf-8")
        )
        stored = manifest.get("manifest_sha256")
        unsigned = dict(manifest)
        unsigned.pop("manifest_sha256", None)
        if stable_sha256(unsigned) != stored:
            raise ValueError("Benchmark manifest SHA-256 mismatch.")
        return manifest

    def prepare_response_workspace(
        self,
        model_id: str,
        *,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        manifest = self._load_manifest()
        root = self.responses_root(model_id)
        if root.exists() and not overwrite:
            raise FileExistsError(
                f"Response workspace already exists; explicit overwrite required: {root}"
            )
        root.mkdir(parents=True, exist_ok=True)

        template = {
            "prediction": 0,
            "confidence": 0,
            "explanation": "",
            "latency_ms": None,
        }
        for case in manifest["cases"]:
            path = root / f"{case['case_id']}.json"
            atomic_write_json(path, template)

        workspace = {
            "schema_version": self.schema_version,
            "experiment_id": self.experiment_id,
            "model_id": model_id,
            "model_slug": slugify_model_id(model_id),
            "benchmark_manifest_sha256": manifest["manifest_sha256"],
            "expected_case_count": manifest["total_case_count"],
            "response_format": {
                "prediction": "integer",
                "confidence": "integer 0..100",
                "explanation": "text",
                "latency_ms": "optional nonnegative number",
            },
        }
        workspace["workspace_sha256"] = stable_sha256(workspace)
        atomic_write_json(root / "workspace.json", workspace)
        return workspace

    def evaluate(
        self,
        model_id: str,
        *,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        manifest = self._load_manifest()
        response_root = self.responses_root(model_id)
        if not response_root.exists():
            raise FileNotFoundError(
                f"Response workspace does not exist: {response_root}"
            )

        output_root = self.evaluation_root(model_id)
        if output_root.exists() and not overwrite:
            raise FileExistsError(
                f"Evaluation output already exists; explicit overwrite required: {output_root}"
            )

        temporary_root = output_root.with_name(f".{output_root.name}.tmp")
        if temporary_root.exists():
            import shutil
            shutil.rmtree(temporary_root)
        temporary_root.mkdir(parents=True)

        records: list[dict[str, Any]] = []
        try:
            for item in manifest["cases"]:
                case_id = item["case_id"]
                private_path = (
                    self.benchmark_root / "cases" / "private" / f"{case_id}.json"
                )
                if not private_path.exists():
                    raise FileNotFoundError(
                        f"Private answer key does not exist: {private_path}"
                    )
                answer = json.loads(private_path.read_text(encoding="utf-8"))
                target = int(answer["target"])
                parsed = self.parser.parse(case_id, response_root / f"{case_id}.json")

                exact_match = (
                    parsed.schema_valid and parsed.prediction == target
                )
                absolute_error = (
                    abs(parsed.prediction - target)
                    if parsed.schema_valid and parsed.prediction is not None
                    else None
                )
                signed_error = (
                    parsed.prediction - target
                    if parsed.schema_valid and parsed.prediction is not None
                    else None
                )
                relative_error = (
                    absolute_error / target
                    if absolute_error is not None and target != 0
                    else None
                )
                prime_valid = (
                    is_prime_64(parsed.prediction)
                    if parsed.schema_valid
                    and parsed.prediction is not None
                    and parsed.prediction > 1
                    else False
                )

                record = {
                    "case_id": case_id,
                    "window_size": int(item["window_size"]),
                    "target_index_1_based": int(item["target_index_1_based"]),
                    "target": target,
                    "response_exists": parsed.response_exists,
                    "valid_json": parsed.valid_json,
                    "schema_valid": parsed.schema_valid,
                    "prediction": parsed.prediction,
                    "confidence": parsed.confidence,
                    "latency_ms": parsed.latency_ms,
                    "exact_match": bool(exact_match),
                    "absolute_error": absolute_error,
                    "relative_error": relative_error,
                    "signed_error": signed_error,
                    "prime_valid_prediction": bool(prime_valid),
                    "parse_error": parsed.parse_error,
                    "response_sha256": parsed.response_sha256,
                    "answer_key_sha256": item["answer_key_sha256"],
                    "public_case_sha256": item["public_case_sha256"],
                    "prompt_sha256": item["prompt_sha256"],
                }
                record["evaluation_sha256"] = stable_sha256(record)
                records.append(record)

            summary = self._summarize(
                model_id=model_id,
                records=records,
                manifest=manifest,
            )
            self._write_outputs(
                temporary_root=temporary_root,
                records=records,
                summary=summary,
            )

            if output_root.exists():
                import shutil
                shutil.rmtree(output_root)
            os.replace(temporary_root, output_root)
            return summary
        except Exception:
            import shutil
            shutil.rmtree(temporary_root, ignore_errors=True)
            raise

    @staticmethod
    def _safe_mean(values: Iterable[float]) -> float | None:
        collected = list(values)
        return mean(collected) if collected else None

    @staticmethod
    def _safe_median(values: Iterable[float]) -> float | None:
        collected = list(values)
        return median(collected) if collected else None

    def _metrics(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(records)
        schema_valid = [r for r in records if r["schema_valid"]]
        numerical = [r for r in schema_valid if r["absolute_error"] is not None]
        confidences = [
            float(r["confidence"]) for r in schema_valid
            if r["confidence"] is not None
        ]
        latencies = [
            float(r["latency_ms"]) for r in schema_valid
            if r["latency_ms"] is not None
        ]

        return {
            "case_count": total,
            "response_exists_count": sum(r["response_exists"] for r in records),
            "valid_json_count": sum(r["valid_json"] for r in records),
            "schema_valid_count": len(schema_valid),
            "correct_count": sum(r["exact_match"] for r in records),
            "exact_accuracy": (
                sum(r["exact_match"] for r in records) / total if total else 0.0
            ),
            "valid_json_rate": (
                sum(r["valid_json"] for r in records) / total if total else 0.0
            ),
            "schema_valid_rate": len(schema_valid) / total if total else 0.0,
            "prime_valid_count": sum(r["prime_valid_prediction"] for r in records),
            "prime_valid_rate": (
                sum(r["prime_valid_prediction"] for r in records) / total
                if total else 0.0
            ),
            "mean_absolute_error": self._safe_mean(
                float(r["absolute_error"]) for r in numerical
            ),
            "median_absolute_error": self._safe_median(
                float(r["absolute_error"]) for r in numerical
            ),
            "mean_relative_error": self._safe_mean(
                float(r["relative_error"]) for r in numerical
                if r["relative_error"] is not None
            ),
            "median_relative_error": self._safe_median(
                float(r["relative_error"]) for r in numerical
                if r["relative_error"] is not None
            ),
            "mean_confidence": self._safe_mean(confidences),
            "median_confidence": self._safe_median(confidences),
            "mean_latency_ms": self._safe_mean(latencies),
            "median_latency_ms": self._safe_median(latencies),
        }

    def _summarize(
        self,
        *,
        model_id: str,
        records: list[dict[str, Any]],
        manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        by_window: dict[str, Any] = {}
        for window in sorted({int(r["window_size"]) for r in records}):
            selected = [r for r in records if int(r["window_size"]) == window]
            by_window[f"W{window:03d}"] = self._metrics(selected)

        summary = {
            "schema_version": self.schema_version,
            "engine_version": self.engine_version,
            "experiment_id": self.experiment_id,
            "model_id": model_id,
            "model_slug": slugify_model_id(model_id),
            "benchmark_manifest_sha256": manifest["manifest_sha256"],
            "dataset_sha256": manifest["dataset_sha256"],
            "overall": self._metrics(records),
            "by_window": by_window,
            "case_results_sha256": stable_sha256(records),
        }
        summary["summary_sha256"] = stable_sha256(summary)
        return summary

    def _write_outputs(
        self,
        *,
        temporary_root: Path,
        records: list[dict[str, Any]],
        summary: dict[str, Any],
    ) -> None:
        atomic_write_json(temporary_root / "summary.json", summary)
        atomic_write_json(temporary_root / "case_results.json", records)

        columns = [
            "case_id", "window_size", "target_index_1_based", "target",
            "prediction", "confidence", "latency_ms", "response_exists",
            "valid_json", "schema_valid", "exact_match", "absolute_error",
            "relative_error", "signed_error", "prime_valid_prediction",
            "parse_error", "response_sha256", "evaluation_sha256",
        ]
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
        atomic_write_text(temporary_root / "case_results.csv", buffer.getvalue())

        overall = summary["overall"]
        markdown = [
            "# PrimeAIExplorer Evaluation",
            "",
            f"- Experiment: `{summary['experiment_id']}`",
            f"- Model: `{summary['model_id']}`",
            f"- Cases: {overall['case_count']}",
            f"- Correct: {overall['correct_count']}",
            f"- Exact accuracy: {overall['exact_accuracy']:.6%}",
            f"- Valid JSON rate: {overall['valid_json_rate']:.6%}",
            f"- Schema-valid rate: {overall['schema_valid_rate']:.6%}",
            f"- Prime-valid prediction rate: {overall['prime_valid_rate']:.6%}",
            "",
            "## Accuracy by window",
            "",
            "| Window | Cases | Correct | Accuracy | Valid JSON | Prime-valid |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
        for window, metrics in summary["by_window"].items():
            markdown.append(
                f"| {window} | {metrics['case_count']} | "
                f"{metrics['correct_count']} | "
                f"{metrics['exact_accuracy']:.6%} | "
                f"{metrics['valid_json_rate']:.6%} | "
                f"{metrics['prime_valid_rate']:.6%} |"
            )
        markdown.extend([
            "",
            f"Summary SHA-256: `{summary['summary_sha256']}`",
            "",
        ])
        atomic_write_text(temporary_root / "summary.md", "\n".join(markdown))


class LeaderboardBuilder:
    schema_version = "1.0"

    def __init__(self, evaluations_root: Path) -> None:
        self.evaluations_root = evaluations_root.resolve()

    def build(self) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        if not self.evaluations_root.exists():
            raise FileNotFoundError(
                f"Evaluations root does not exist: {self.evaluations_root}"
            )

        for summary_path in sorted(
            self.evaluations_root.glob("*/summary.json")
        ):
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            overall = summary["overall"]
            entries.append({
                "model_id": summary["model_id"],
                "model_slug": summary["model_slug"],
                "case_count": overall["case_count"],
                "correct_count": overall["correct_count"],
                "exact_accuracy": overall["exact_accuracy"],
                "valid_json_rate": overall["valid_json_rate"],
                "schema_valid_rate": overall["schema_valid_rate"],
                "prime_valid_rate": overall["prime_valid_rate"],
                "mean_absolute_error": overall["mean_absolute_error"],
                "mean_confidence": overall["mean_confidence"],
                "summary_sha256": summary["summary_sha256"],
            })

        entries.sort(
            key=lambda item: (
                -item["exact_accuracy"],
                -(item["schema_valid_rate"]),
                item["model_id"].casefold(),
            )
        )
        leaderboard = {
            "schema_version": self.schema_version,
            "model_count": len(entries),
            "entries": entries,
        }
        leaderboard["leaderboard_sha256"] = stable_sha256(leaderboard)
        return leaderboard

    def write(self, output_root: Path) -> dict[str, Any]:
        leaderboard = self.build()
        output_root.mkdir(parents=True, exist_ok=True)
        atomic_write_json(output_root / "leaderboard.json", leaderboard)

        columns = [
            "rank", "model_id", "case_count", "correct_count", "exact_accuracy",
            "valid_json_rate", "schema_valid_rate", "prime_valid_rate",
            "mean_absolute_error", "mean_confidence", "summary_sha256",
        ]
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns)
        writer.writeheader()
        for rank, entry in enumerate(leaderboard["entries"], start=1):
            writer.writerow({"rank": rank, **entry})
        atomic_write_text(output_root / "leaderboard.csv", buffer.getvalue())
        return leaderboard
