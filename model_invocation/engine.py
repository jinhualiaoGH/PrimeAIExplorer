from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from model_providers import ModelRequest, ProviderResponse, default_registry
from model_providers.bridge import _parse

from .io import read_json, read_jsonl, write_json_atomic, write_jsonl_atomic


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_provider_configuration(path: str | Path) -> dict[str, Any]:
    config = read_json(path)
    provider = str(config.get("provider", "")).strip().lower()
    model = str(config.get("model", "")).strip()
    if not provider:
        raise ValueError("provider configuration requires 'provider'")
    if not model:
        raise ValueError("provider configuration requires 'model'")
    options = config.get("options", {})
    if not isinstance(options, dict):
        raise ValueError("provider configuration 'options' must be an object")
    return {
        "provider": provider,
        "model": model,
        "system_prompt": config.get("system_prompt"),
        "temperature": config.get("temperature", 0.0),
        "max_output_tokens": config.get("max_output_tokens"),
        "seed": config.get("seed"),
        "json_mode": bool(config.get("json_mode", True)),
        "options": options,
    }


@dataclass(frozen=True, slots=True)
class InvocationSummary:
    provider: str
    model: str
    input_count: int
    attempted_count: int
    completed_count: int
    skipped_count: int
    failed_count: int
    output_path: str
    manifest_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InvocationEngine:
    def __init__(self, provider_config: Mapping[str, Any], provider=None):
        self.config = dict(provider_config)
        self.provider = provider or default_registry().create(
            str(self.config["provider"]), **dict(self.config.get("options", {}))
        )

    def _request(self, record: Mapping[str, Any]) -> ModelRequest:
        prompt = record.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("each input record requires a non-empty 'prompt'")
        metadata = dict(record.get("metadata", {})) if isinstance(record.get("metadata"), dict) else {}
        case_id = str(record.get("case_id", "")).strip()
        prompt_sha256 = str(record.get("prompt_sha256", "")).strip() or sha256_text(prompt)
        if case_id:
            metadata["case_id"] = case_id
        metadata["prompt_sha256"] = prompt_sha256
        return ModelRequest(
            prompt=prompt,
            model=str(record.get("model") or self.config["model"]),
            system_prompt=record.get("system_prompt", self.config.get("system_prompt")),
            temperature=record.get("temperature", self.config.get("temperature", 0.0)),
            max_output_tokens=record.get("max_output_tokens", self.config.get("max_output_tokens")),
            seed=record.get("seed", self.config.get("seed")),
            json_mode=bool(record.get("json_mode", self.config.get("json_mode", True))),
            metadata=metadata,
        )

    @staticmethod
    def _normalized_record(source: Mapping[str, Any], response: ProviderResponse) -> dict[str, Any]:
        prediction, confidence = _parse(response.text)
        actual = source.get("actual_value")
        actual = actual if isinstance(actual, int) else None
        case_id = str(source.get("case_id", "")).strip()
        if not case_id:
            case_id = "CASE-" + sha256_text(str(source.get("prompt", "")))[:16].upper()
        return {
            "case_id": case_id,
            "sequence_index": source.get("sequence_index"),
            "window_size": source.get("window_size"),
            "response_text": response.text,
            "parsed_prediction": prediction,
            "actual_value": actual,
            "is_correct": prediction == actual if prediction is not None and actual is not None else None,
            "confidence": confidence,
            "latency_seconds": response.latency_seconds,
            "successful": prediction is not None,
            "provider_request_id": response.request_id,
            "metadata": {
                "provider": response.provider,
                "provider_model": response.model,
                "finish_reason": response.finish_reason,
                "usage": response.usage.to_dict(),
                "prompt_sha256": response.metadata.get("prompt_sha256")
                if isinstance(response.metadata, Mapping)
                else None,
            },
        }

    def run(
        self,
        input_path: str | Path,
        output_path: str | Path,
        *,
        manifest_path: str | Path | None = None,
        resume: bool = True,
        force: bool = False,
        stop_on_error: bool = False,
    ) -> InvocationSummary:
        input_records = read_jsonl(input_path)
        destination = Path(output_path)
        manifest = Path(manifest_path) if manifest_path else destination.with_suffix(".manifest.json")
        existing = read_jsonl(destination) if resume and destination.exists() and not force else []
        by_case = {str(item.get("case_id")): item for item in existing if item.get("case_id")}
        output_records = list(existing)
        attempted = completed = skipped = failed = 0
        failures: list[dict[str, Any]] = []
        started_at = utc_now()

        for source in input_records:
            case_id = str(source.get("case_id", "")).strip()
            if case_id and case_id in by_case and not force:
                skipped += 1
                continue
            attempted += 1
            try:
                request = self._request(source)
                response = self.provider.generate(request)
                normalized = self._normalized_record(source, response)
                if case_id and case_id in by_case:
                    output_records = [item for item in output_records if str(item.get("case_id")) != case_id]
                output_records.append(normalized)
                by_case[normalized["case_id"]] = normalized
                completed += 1
            except Exception as exc:
                failed += 1
                failures.append({"case_id": case_id or None, "error_type": type(exc).__name__, "message": str(exc)})
                if stop_on_error:
                    break

        output_records.sort(key=lambda item: str(item.get("case_id", "")))
        write_jsonl_atomic(destination, output_records)
        manifest_value = {
            "schema_version": "1.0",
            "generated_at_utc": utc_now(),
            "started_at_utc": started_at,
            "provider": self.config["provider"],
            "model": self.config["model"],
            "input_path": str(Path(input_path).resolve()),
            "output_path": str(destination.resolve()),
            "input_count": len(input_records),
            "attempted_count": attempted,
            "completed_count": completed,
            "skipped_count": skipped,
            "failed_count": failed,
            "output_record_count": len(output_records),
            "failures": failures,
        }
        write_json_atomic(manifest, manifest_value)
        return InvocationSummary(
            provider=str(self.config["provider"]),
            model=str(self.config["model"]),
            input_count=len(input_records),
            attempted_count=attempted,
            completed_count=completed,
            skipped_count=skipped,
            failed_count=failed,
            output_path=str(destination),
            manifest_path=str(manifest),
        )
