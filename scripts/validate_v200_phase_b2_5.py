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


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<38} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    print("PrimeAIExplorer v2.0 Phase B2.5 Validator")
    print("=" * 98)
    check("installed version", version == "2.0.0-phase-b2.5", version)

    context = ExecutionContext.create(
        benchmark_id="b25-validation",
        benchmark_version="1.0.0",
        connector_id="dataset",
        software_version=version,
        project_root=ROOT,
        working_directory=ROOT / "runtime" / "b25-validation",
        output_directory=ROOT / "runtime" / "b25-validation-output",
        configuration={},
        session_id="RUN-B25-VALIDATION",
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
            capabilities=("dataset.describe", "dataset.case", "dataset.batch"),
            enabled=True,
            configuration={
                "providers": [{
                    "provider_type": "in_memory",
                    "sequence_id": "prime-gap",
                    "values": [2, 4, 2, 6, 6, 8, 4, 2, 10, 12, 2, 16],
                    "index_origin": 1,
                    "title": "Validation prime gaps",
                }],
                "datasets": [{
                    "schema_version": "1.0",
                    "dataset_id": "next-gap-w4",
                    "dataset_version": "1.0.0",
                    "sequence_id": "prime-gap",
                    "title": "Next-gap continuation fixture",
                    "start_index": 1,
                    "case_count": 6,
                    "observation_count": 4,
                    "target_count": 1,
                    "stride": 1,
                    "metadata": {"task": "next-value prediction"},
                }],
            },
        )
    )

    engine = ExecutionEngine(session=session)
    pipeline = PluginExecutionPipeline(engine, registry)
    try:
        describe_record = pipeline.execute(
            execution_id="EXEC-B25-DESCRIBE",
            capability="dataset.describe",
            payload={"operation": "dataset.describe", "dataset_id": "next-gap-w4"},
        )
        case_record = pipeline.execute(
            execution_id="EXEC-B25-CASE",
            capability="dataset.case",
            payload={
                "operation": "dataset.case",
                "dataset_id": "next-gap-w4",
                "case_index": 3,
            },
        )
        batch_record = pipeline.execute(
            execution_id="EXEC-B25-BATCH",
            capability="dataset.batch",
            payload={
                "operation": "dataset.batch",
                "requests": [
                    {"dataset_id": "next-gap-w4", "case_index": 0},
                    {"dataset_id": "next-gap-w4", "case_index": 1},
                ],
            },
        )
        descriptor = engine.output("EXEC-B25-DESCRIBE")
        case = engine.output("EXEC-B25-CASE")
        batch = engine.output("EXEC-B25-BATCH")

        check("dataset plugin loaded", pipeline.loader.loaded_ids() == ("sequence_api",), "sequence_api")
        check("dataset descriptor", describe_record.success and descriptor["validated"], descriptor["dataset"]["dataset_id"])
        check("dataset identity", len(descriptor["dataset_sha256"]) == 64, descriptor["dataset_sha256"][:16])
        check("case execution", case_record.success, case["case_id"])
        check("observation window", case["observation"] == [6, 6, 8, 4], str(case["observation"]))
        check("target window", case["target"] == [2], str(case["target"]))
        check("index contract", case["start_index"] == 4 and case["target_start_index"] == 8, "4 -> 8")
        check("case identity", len(case["metadata"]["case_sha256"]) == 64, case["metadata"]["case_sha256"][:16])
        check("batch execution", batch_record.success, str(len(batch["cases"])))
        check("batch identity", len(batch["batch_sha256"]) == 64, batch["batch_sha256"][:16])
    finally:
        pipeline.close_plugin("sequence_api")

    print("=" * 98)
    print("PrimeAIExplorer v2.0 Phase B2.5 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
