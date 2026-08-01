from __future__ import annotations

import json
from pathlib import Path

from model_invocation.engine import InvocationEngine, load_provider_configuration
from model_providers import ProviderCapabilities, ProviderResponse, ProviderUsage


class FakeProvider:
    name = "fake"
    capabilities = ProviderCapabilities(True, True, True)

    def __init__(self):
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        case_id = request.metadata["case_id"]
        prediction = 6 if case_id.endswith("1") else 10
        return ProviderResponse(
            "fake",
            request.model,
            json.dumps({"prediction": prediction, "confidence": 80}),
            0.25,
            request_id=f"REQ-{self.calls}",
            finish_reason="completed",
            usage=ProviderUsage(3, 2, 5),
        )


def write_cases(path: Path) -> None:
    path.write_text(
        '{"case_id":"C1","prompt":"p1","actual_value":6,"window_size":8}\n'
        '{"case_id":"C2","prompt":"p2","actual_value":10,"window_size":8}\n',
        encoding="utf-8",
    )


def test_configuration_validation(tmp_path: Path) -> None:
    path = tmp_path / "provider.json"
    path.write_text('{"provider":"manual","model":"m","options":{}}', encoding="utf-8")
    assert load_provider_configuration(path)["provider"] == "manual"


def test_normalized_output_is_metrics_compatible(tmp_path: Path) -> None:
    cases = tmp_path / "cases.jsonl"
    output = tmp_path / "responses.jsonl"
    write_cases(cases)
    provider = FakeProvider()
    summary = InvocationEngine({"provider": "fake", "model": "m"}, provider=provider).run(cases, output)
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert summary.completed_count == 2
    assert records[0]["parsed_prediction"] == 6
    assert records[0]["metadata"]["usage"]["total_tokens"] == 5


def test_resume_skips_completed_cases(tmp_path: Path) -> None:
    cases = tmp_path / "cases.jsonl"
    output = tmp_path / "responses.jsonl"
    write_cases(cases)
    provider = FakeProvider()
    engine = InvocationEngine({"provider": "fake", "model": "m"}, provider=provider)
    engine.run(cases, output)
    second = engine.run(cases, output)
    assert second.skipped_count == 2
    assert provider.calls == 2


def test_force_reinvokes_cases(tmp_path: Path) -> None:
    cases = tmp_path / "cases.jsonl"
    output = tmp_path / "responses.jsonl"
    write_cases(cases)
    provider = FakeProvider()
    engine = InvocationEngine({"provider": "fake", "model": "m"}, provider=provider)
    engine.run(cases, output)
    forced = engine.run(cases, output, force=True)
    assert forced.attempted_count == 2
    assert provider.calls == 4


def test_manifest_records_failures(tmp_path: Path) -> None:
    class Broken(FakeProvider):
        def generate(self, request):
            raise RuntimeError("controlled")

    cases = tmp_path / "cases.jsonl"
    output = tmp_path / "responses.jsonl"
    manifest = tmp_path / "manifest.json"
    write_cases(cases)
    summary = InvocationEngine({"provider": "fake", "model": "m"}, provider=Broken()).run(
        cases, output, manifest_path=manifest
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    assert summary.failed_count == 2
    assert value["failures"][0]["error_type"] == "RuntimeError"


def test_stop_on_error_stops_after_first_failure(tmp_path: Path) -> None:
    class Broken(FakeProvider):
        def generate(self, request):
            raise RuntimeError("controlled")

    cases = tmp_path / "cases.jsonl"
    output = tmp_path / "responses.jsonl"
    write_cases(cases)
    summary = InvocationEngine({"provider": "fake", "model": "m"}, provider=Broken()).run(
        cases, output, stop_on_error=True
    )
    assert summary.attempted_count == 1
    assert summary.failed_count == 1
