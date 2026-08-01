from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from execution import ExecutionEngine
from kernel import ExecutionContext
from plugin_runtime import ManifestRegistry, PluginExecutionPipeline, PluginManifest
from runtime import RuntimeConfiguration, RuntimeSession


SYSTEM_TEMPLATE = (
    "You are participating in a controlled numerical continuation experiment. "
    "Follow the response format exactly."
)

USER_TEMPLATE = """You are given a sequence of consecutive prime gaps.

Observation window size: {observation_count}

Observed gaps:
{observed_values}

Predict the next prime gap.

Return JSON only using this exact structure:

{response_schema}
"""


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<38} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    print("PrimeAIExplorer v2.0 Phase B2.6 Validator")
    print("=" * 100)
    check("installed version", version == "2.0.0-phase-b2.6", version)

    context = ExecutionContext.create(
        benchmark_id="b26-validation",
        benchmark_version="1.0.0",
        connector_id="prompt",
        software_version=version,
        project_root=ROOT,
        working_directory=ROOT / "runtime" / "b26-validation",
        output_directory=ROOT / "runtime" / "b26-validation-output",
        configuration={},
        session_id="RUN-B26-VALIDATION",
    )
    session = RuntimeSession(
        context=context,
        configuration=RuntimeConfiguration.empty(),
    )
    session.initialize()
    session.start()

    registry = ManifestRegistry()
    registry.register(
        PluginManifest(
            schema_version="1.0",
            plugin_id="sequence_api",
            plugin_version=version,
            module="sequence_api.adapter",
            class_name="SequenceExecutionPlugin",
            capabilities=(
                "prompt.template.describe",
                "prompt.generate",
                "prompt.batch",
            ),
            enabled=True,
            configuration={
                "providers": [{
                    "provider_type": "in_memory",
                    "sequence_id": "prime-gap",
                    "values": [6, 18, 4, 6, 6, 6, 2, 6, 4, 8],
                    "index_origin": 1,
                    "title": "Validation gaps",
                }],
                "datasets": [{
                    "dataset_id": "next-gap-w8",
                    "sequence_id": "prime-gap",
                    "start_index": 1,
                    "case_count": 2,
                    "observation_count": 8,
                    "target_count": 1,
                    "stride": 1,
                }],
                "prompt_templates": [{
                    "template_id": "prime-gap-json-v1",
                    "template_version": "1.0.0",
                    "title": "Prime-gap continuation JSON prompt",
                    "system_template": SYSTEM_TEMPLATE,
                    "user_template": USER_TEMPLATE,
                    "response_schema": {
                        "prediction": "<integer>",
                        "confidence": "<integer from 0 to 100>",
                        "explanation": "<brief explanation>",
                    },
                }],
            },
        )
    )

    engine = ExecutionEngine(session=session)
    pipeline = PluginExecutionPipeline(engine, registry)
    try:
        template_record = pipeline.execute(
            execution_id="EXEC-B26-TEMPLATE",
            capability="prompt.template.describe",
            payload={
                "operation": "prompt.template.describe",
                "template_id": "prime-gap-json-v1",
            },
        )
        prompt_record = pipeline.execute(
            execution_id="EXEC-B26-PROMPT",
            capability="prompt.generate",
            payload={
                "operation": "prompt.generate",
                "dataset_id": "next-gap-w8",
                "case_index": 0,
                "template_id": "prime-gap-json-v1",
            },
        )
        audit_record = pipeline.execute(
            execution_id="EXEC-B26-AUDIT",
            capability="prompt.generate",
            payload={
                "operation": "prompt.generate",
                "dataset_id": "next-gap-w8",
                "case_index": 0,
                "template_id": "prime-gap-json-v1",
                "include_ground_truth": True,
            },
        )
        batch_record = pipeline.execute(
            execution_id="EXEC-B26-BATCH",
            capability="prompt.batch",
            payload={
                "operation": "prompt.batch",
                "requests": [
                    {
                        "dataset_id": "next-gap-w8",
                        "case_index": 0,
                        "template_id": "prime-gap-json-v1",
                    },
                    {
                        "dataset_id": "next-gap-w8",
                        "case_index": 1,
                        "template_id": "prime-gap-json-v1",
                    },
                ],
            },
        )

        template = engine.output("EXEC-B26-TEMPLATE")
        prompt = engine.output("EXEC-B26-PROMPT")
        audit = engine.output("EXEC-B26-AUDIT")
        batch = engine.output("EXEC-B26-BATCH")

        check("prompt plugin loaded", pipeline.loader.loaded_ids() == ("sequence_api",), "sequence_api")
        check("template descriptor", template_record.success, template["template_id"])
        check("template identity", len(template["template_sha256"]) == 64, template["template_sha256"][:16])
        check("prompt execution", prompt_record.success, prompt["prompt_id"])
        check("system message", prompt["system_message"] == SYSTEM_TEMPLATE, "stable")
        check("observation rendering", "6 18 4 6 6 6 2 6" in prompt["user_message"], "8 gaps")
        check("response contract", '"prediction": "<integer>"' in prompt["user_message"], "JSON schema")
        check("ground truth hidden", "ground_truth" not in prompt, "hidden")
        check("audit ground truth", audit_record.success and audit["ground_truth"] == [4], str(audit["ground_truth"]))
        check("prompt identity", len(prompt["prompt_sha256"]) == 64, prompt["prompt_sha256"][:16])
        check("batch execution", batch_record.success and len(batch["prompts"]) == 2, str(len(batch["prompts"])))
        check("batch identity", len(batch["batch_sha256"]) == 64, batch["batch_sha256"][:16])
    finally:
        pipeline.close_plugin("sequence_api")

    print("=" * 100)
    print("PrimeAIExplorer v2.0 Phase B2.6 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
