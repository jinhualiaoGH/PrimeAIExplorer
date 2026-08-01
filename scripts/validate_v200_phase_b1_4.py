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

    print("PrimeAIExplorer v2.0 Phase B1.4 Validator")
    print("=" * 84)
    check("installed version", version == "2.0.0-phase-b1.4", version)

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        context = ExecutionContext.create(
            benchmark_id="b14-validation",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version=version,
            project_root=ROOT,
            working_directory=path,
            output_directory=path / "output",
            configuration={},
            session_id="RUN-B14-VALIDATION",
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
                plugin_id="echo",
                plugin_version="1.0.0",
                module="tests.fixtures.b14_plugins",
                class_name="EchoPlugin",
                capabilities=("echo",),
                enabled=True,
                configuration={"prefix": "validated"},
            )
        )

        engine = ExecutionEngine(session=session)
        pipeline = PluginExecutionPipeline(engine, registry)
        record = pipeline.execute(
            execution_id="EXEC-B14-VALIDATION",
            capability="echo",
            payload={"value": 101},
        )

        output = engine.output("EXEC-B14-VALIDATION")
        check("manifest registry", registry.registered_ids() == ("echo",), "echo")
        check("capability resolver", pipeline.resolver.resolve("echo").plugin_id == "echo", "echo")
        check("plugin loader", pipeline.loader.loaded_ids() == ("echo",), "echo")
        check("plugin lifecycle", pipeline.lifecycle("echo").state.value == "ready", "ready")
        check("pipeline execution", record.success, record.output_sha256[:16])
        check("pipeline output", output["prefix"] == "validated", "validated")
        check("pipeline snapshot", len(pipeline.snapshot()["engine_snapshot_sha256"]) == 64, "stable")

    print("=" * 84)
    print("PrimeAIExplorer v2.0 Phase B1.4 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
