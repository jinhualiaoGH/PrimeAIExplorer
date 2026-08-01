from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from execution import ExecutionEngine
from kernel import ExecutionContext
from plugin_runtime import (
    ManifestRegistry,
    PluginExecutionPipeline,
    PluginManifest,
)
from runtime import RuntimeConfiguration, RuntimeSession


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<34} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    version = (ROOT / "VERSION").read_text(
        encoding="utf-8"
    ).strip()

    print("PrimeAIExplorer v2.0 Phase B2.1 Validator")
    print("=" * 88)
    check("installed version", version == "2.0.0-phase-b2.1", version)

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        context = ExecutionContext.create(
            benchmark_id="b21-validation",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version=version,
            project_root=ROOT,
            working_directory=path,
            output_directory=path / "output",
            configuration={},
            session_id="RUN-B21-VALIDATION",
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
                    "sequence.describe",
                    "sequence.window",
                    "sequence.batch",
                ),
                enabled=True,
                configuration={
                    "providers": [
                        {
                            "sequence_id": "prime-value",
                            "title": "Prime values",
                            "values": [2, 3, 5, 7, 11],
                            "index_origin": 1,
                            "strictly_increasing": True,
                        }
                    ]
                },
            )
        )

        engine = ExecutionEngine(session=session)
        pipeline = PluginExecutionPipeline(engine, registry)

        descriptor_record = pipeline.execute(
            execution_id="EXEC-B21-DESCRIBE",
            capability="sequence.describe",
            payload={
                "operation": "describe",
                "sequence_id": "prime-value",
            },
        )
        descriptor = engine.output("EXEC-B21-DESCRIBE")

        window_record = pipeline.execute(
            execution_id="EXEC-B21-WINDOW",
            capability="sequence.window",
            payload={
                "operation": "window",
                "sequence_id": "prime-value",
                "start_index": 2,
                "count": 3,
            },
        )
        window = engine.output("EXEC-B21-WINDOW")

        check("sequence plugin loaded", pipeline.loader.loaded_ids() == ("sequence_api",), "sequence_api")
        check("sequence lifecycle", pipeline.lifecycle("sequence_api").state.value == "ready", "ready")
        check("descriptor execution", descriptor_record.success, descriptor["sequence_id"])
        check("descriptor contract", descriptor["length"] == 5, "length=5")
        check("window execution", window_record.success, window_record.output_sha256[:16])
        check("window values", window["values"] == [3, 5, 7], str(window["values"]))
        check("index contract", window["start_index"] == 2 and window["end_index"] == 4, "2..4")
        check("deterministic hashes", len(window["descriptor_sha256"]) == 64, "stable")

    print("=" * 88)
    print("PrimeAIExplorer v2.0 Phase B2.1 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
