from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from execution import ExecutionEngine, ExecutionRequest
from kernel import ExecutionContext
from runtime import RuntimeConfiguration, RuntimeSession


class EchoPlugin:
    plugin_id = "echo"

    def execute(self, payload, context):
        return {
            "benchmark_id": context.benchmark_id,
            "payload": payload,
        }


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<34} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    version = (ROOT / "VERSION").read_text(
        encoding="utf-8"
    ).strip()

    print("PrimeAIExplorer v2.0 Phase B1.3 Validator")
    print("=" * 84)
    check("installed version", version == "2.0.0-phase-b1.3", version)

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        context = ExecutionContext.create(
            benchmark_id="validation",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version=version,
            project_root=ROOT,
            working_directory=path,
            output_directory=path / "output",
            configuration={},
            session_id="RUN-B13-VALIDATION",
        )
        session = RuntimeSession(
            context=context,
            configuration=RuntimeConfiguration.empty(),
        )
        session.initialize()
        session.start()

        engine = ExecutionEngine(session=session)
        engine.dispatcher.register(EchoPlugin())

        request = ExecutionRequest.create(
            execution_id="EXEC-000001",
            plugin_id="echo",
            session_id=context.session_id,
            payload={"value": 101},
        )
        engine.submit(request)
        record = engine.execute_next()

        check("dispatcher", engine.dispatcher.registered_ids() == ("echo",), "echo")
        check("scheduler", engine.scheduler.pending_count() == 0, "empty")
        check("execution success", record.success, record.output_sha256[:16])
        check("metrics", engine.metrics.succeeded_count == 1, "1 succeeded")
        check("deterministic output", engine.output("EXEC-000001")["payload"]["value"] == 101, "101")
        check("engine snapshot", len(engine.snapshot_sha256) == 64, engine.snapshot_sha256[:16])

    print("=" * 84)
    print("PrimeAIExplorer v2.0 Phase B1.3 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
