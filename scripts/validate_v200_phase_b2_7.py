from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel import ExecutionContext
from runtime import RuntimeConfiguration, RuntimeSession
from sequence_api import SequenceExecutionPlugin


SYSTEM_TEMPLATE = "Controlled experiment."
USER_TEMPLATE = "{observation_count}\n{observed_values}\n{response_schema}"


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<38} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    print("PrimeAIExplorer v2.0 Phase B2.7 Validator")
    print("=" * 100)
    check("installed version", version == "2.0.0-phase-b2.7", version)

    context = ExecutionContext.create(
        benchmark_id="b27-validation",
        benchmark_version="1.0.0",
        connector_id="response-evaluation",
        software_version=version,
        project_root=ROOT,
        working_directory=ROOT / "runtime" / "b27-validation",
        output_directory=ROOT / "runtime" / "b27-validation-output",
        configuration={},
        session_id="RUN-B27-VALIDATION",
    )
    session = RuntimeSession(
        context=context,
        configuration=RuntimeConfiguration.empty(),
    )
    session.initialize()
    session.start()

    plugin = SequenceExecutionPlugin({
        "providers": [{
            "provider_type": "in_memory",
            "sequence_id": "prime-gap",
            "values": [6, 18, 4, 6, 6, 6, 2, 6, 4, 8],
            "index_origin": 1,
        }],
        "datasets": [{
            "dataset_id": "next-gap-w8",
            "sequence_id": "prime-gap",
            "start_index": 1,
            "case_count": 2,
            "observation_count": 8,
            "target_count": 1,
        }],
        "prompt_templates": [{
            "template_id": "prime-gap-json-v1",
            "system_template": SYSTEM_TEMPLATE,
            "user_template": USER_TEMPLATE,
            "response_schema": {
                "prediction": "<integer>",
                "confidence": "<integer from 0 to 100>",
                "explanation": "<brief explanation>",
            },
        }],
    })

    try:
        prompt0 = plugin.execute({
            "operation": "prompt.generate",
            "dataset_id": "next-gap-w8",
            "case_index": 0,
            "template_id": "prime-gap-json-v1",
        }, context)
        prompt1 = plugin.execute({
            "operation": "prompt.generate",
            "dataset_id": "next-gap-w8",
            "case_index": 1,
            "template_id": "prime-gap-json-v1",
        }, context)

        parsed = plugin.execute({
            "operation": "response.parse",
            "response_text": '{"prediction":4,"confidence":90,"explanation":"local continuation"}',
        }, context)

        exact = plugin.execute({
            "operation": "response.evaluate",
            "dataset_id": "next-gap-w8",
            "case_index": 0,
            "template_id": "prime-gap-json-v1",
            "prompt_id": prompt0["prompt_id"],
            "response_text": '{"prediction":4,"confidence":90,"explanation":"local continuation"}',
            "model_id": "validator-model",
        }, context)

        batch = plugin.execute({
            "operation": "response.evaluate_batch",
            "items": [
                {
                    "dataset_id": "next-gap-w8",
                    "case_index": 0,
                    "template_id": "prime-gap-json-v1",
                    "prompt_id": prompt0["prompt_id"],
                    "response_text": '{"prediction":4,"confidence":90,"explanation":"local continuation"}',
                    "model_id": "validator-model",
                },
                {
                    "dataset_id": "next-gap-w8",
                    "case_index": 1,
                    "template_id": "prime-gap-json-v1",
                    "prompt_id": prompt1["prompt_id"],
                    "response_text": '{"prediction":6,"confidence":50,"explanation":"local continuation"}',
                    "model_id": "validator-model",
                },
            ],
        }, context)

        check("response parser", parsed["prediction"] == 4, str(parsed["prediction"]))
        check("confidence contract", parsed["confidence"] == 90, str(parsed["confidence"]))
        check("exact match", exact["exact_match"] is True, str(exact["exact_match"]))
        check("target recovery", exact["target"] == 4, str(exact["target"]))
        check("absolute error", exact["absolute_error"] == 0.0, str(exact["absolute_error"]))
        check("confidence error", exact["confidence_error"] == 10.0, str(exact["confidence_error"]))
        check("evaluation identity", len(exact["evaluation_sha256"]) == 64, exact["evaluation_sha256"][:16])
        check("batch count", batch["summary"]["count"] == 2, str(batch["summary"]["count"]))
        check("batch exact count", batch["summary"]["exact_match_count"] == 1, str(batch["summary"]["exact_match_count"]))
        check("batch exact rate", batch["summary"]["exact_match_rate"] == 0.5, str(batch["summary"]["exact_match_rate"]))
        check("batch identity", len(batch["batch_sha256"]) == 64, batch["batch_sha256"][:16])
    finally:
        plugin.close()

    print("=" * 100)
    print("PrimeAIExplorer v2.0 Phase B2.7 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
