from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel import ExecutionContext, ExecutionResult
from runtime import (
    RuntimeConfiguration,
    RuntimeSession,
    RuntimeState,
)


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<34} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    version = (ROOT / "VERSION").read_text(
        encoding="utf-8"
    ).strip()

    print("PrimeAIExplorer v2.0 Phase B1.2 Validator")
    print("=" * 84)
    check("installed version", version == "2.0.0-phase-b1.2", version)

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        context = ExecutionContext.create(
            benchmark_id="prime_value",
            benchmark_version="2.0.0",
            connector_id="mock",
            software_version=version,
            project_root=ROOT,
            working_directory=path,
            output_directory=path / "output",
            configuration={},
            session_id="RUN-B12-VALIDATION",
        )
        configuration = RuntimeConfiguration.from_mapping(
            {"mode": "validation"}
        )
        session = RuntimeSession(
            context=context,
            configuration=configuration,
        )

        check(
            "initial runtime state",
            session.state is RuntimeState.CREATED,
            session.state.value,
        )

        session.services.register("configuration", configuration)
        check(
            "service registry",
            session.services.contains("configuration"),
            ",".join(session.services.registered_ids()),
        )

        session.initialize()
        session.start()
        result = ExecutionResult.success(
            session_id=context.session_id,
            elapsed_seconds=0.01,
            response_count=1,
            evaluation_count=1,
        )
        session.finish(result)

        check(
            "final runtime state",
            session.state is RuntimeState.FINISHED,
            session.state.value,
        )
        check(
            "runtime event count",
            len(session.events.history()) == 5,
            str(len(session.events.history())),
        )
        check(
            "runtime snapshot",
            len(session.snapshot_sha256) == 64,
            session.snapshot_sha256[:16],
        )

    print("=" * 84)
    print("PrimeAIExplorer v2.0 Phase B1.2 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
