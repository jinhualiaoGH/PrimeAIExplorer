from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from execution import (
    ExecutionEngine,
    ExecutionRequest,
    ExecutionScheduler,
    PluginDispatcher,
)
from kernel import (
    ConfigurationError,
    ExecutionContext,
    RunnerError,
    ValidationError,
)
from runtime import RuntimeConfiguration, RuntimeSession


class EchoPlugin:
    plugin_id = "echo"

    def execute(self, payload, context):
        return {
            "payload": payload,
            "benchmark_id": context.benchmark_id,
        }


class FailingPlugin:
    plugin_id = "fail"

    def execute(self, payload, context):
        raise ValueError("intentional failure")


class InvalidPlugin:
    plugin_id = "invalid"


class ExecutionEngineTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="benchmark",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b1.3",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B13-TEST",
            created_utc="2026-07-31T12:00:00.000000Z",
        )
        return RuntimeSession(
            context=context,
            configuration=RuntimeConfiguration.empty(),
        )

    def request(
        self,
        execution_id: str = "EXEC-000001",
        plugin_id: str = "echo",
    ) -> ExecutionRequest:
        return ExecutionRequest.create(
            execution_id=execution_id,
            plugin_id=plugin_id,
            session_id="RUN-B13-TEST",
            payload={"value": 101},
            metadata={"window_size": 8},
        )

    def test_request_hash_is_stable(self) -> None:
        self.assertEqual(
            self.request().request_sha256,
            self.request().request_sha256,
        )

    def test_request_metadata_is_immutable(self) -> None:
        request = self.request()
        with self.assertRaises(TypeError):
            request.metadata["x"] = 1

    def test_dispatcher_register_and_resolve(self) -> None:
        dispatcher = PluginDispatcher()
        plugin = EchoPlugin()
        dispatcher.register(plugin)
        self.assertIs(dispatcher.resolve("echo"), plugin)

    def test_dispatcher_duplicate_rejected(self) -> None:
        dispatcher = PluginDispatcher()
        dispatcher.register(EchoPlugin())
        with self.assertRaises(ConfigurationError):
            dispatcher.register(EchoPlugin())

    def test_dispatcher_invalid_plugin_rejected(self) -> None:
        dispatcher = PluginDispatcher()
        with self.assertRaises(ConfigurationError):
            dispatcher.register(InvalidPlugin())

    def test_dispatcher_ids_are_sorted(self) -> None:
        class Z:
            plugin_id = "z"
            def execute(self, payload, context):
                return payload
        dispatcher = PluginDispatcher()
        dispatcher.register(Z())
        dispatcher.register(EchoPlugin())
        self.assertEqual(dispatcher.registered_ids(), ("echo", "z"))

    def test_scheduler_fifo(self) -> None:
        scheduler = ExecutionScheduler()
        scheduler.submit(self.request("EXEC-1"))
        scheduler.submit(self.request("EXEC-2"))
        self.assertEqual(scheduler.next_request().execution_id, "EXEC-1")
        self.assertEqual(scheduler.next_request().execution_id, "EXEC-2")

    def test_scheduler_duplicate_execution_rejected(self) -> None:
        scheduler = ExecutionScheduler()
        scheduler.submit(self.request())
        with self.assertRaises(ConfigurationError):
            scheduler.submit(self.request())

    def test_scheduler_empty_rejected(self) -> None:
        with self.assertRaises(ConfigurationError):
            ExecutionScheduler().next_request()

    def test_submit_requires_matching_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = ExecutionEngine(session=session)
            wrong = ExecutionRequest.create(
                execution_id="EXEC-X",
                plugin_id="echo",
                session_id="OTHER",
                payload={},
            )
            with self.assertRaises(ValidationError):
                engine.submit(wrong)

    def test_execution_requires_running_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = ExecutionEngine(session=session)
            engine.dispatcher.register(EchoPlugin())
            engine.submit(self.request())
            with self.assertRaises(ValidationError):
                engine.execute_next()

    def test_successful_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            session.initialize()
            session.start()
            engine = ExecutionEngine(session=session)
            engine.dispatcher.register(EchoPlugin())
            engine.submit(self.request())
            record = engine.execute_next()
            self.assertTrue(record.success)
            self.assertEqual(
                engine.output("EXEC-000001")["payload"]["value"],
                101,
            )

    def test_failed_execution_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            session.initialize()
            session.start()
            engine = ExecutionEngine(session=session)
            engine.dispatcher.register(FailingPlugin())
            engine.submit(self.request(plugin_id="fail"))
            with self.assertRaises(RunnerError):
                engine.execute_next()
            self.assertEqual(len(engine.records()), 1)
            self.assertFalse(engine.records()[0].success)
            self.assertEqual(engine.metrics.failed_count, 1)

    def test_execute_all_preserves_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            session.initialize()
            session.start()
            engine = ExecutionEngine(session=session)
            engine.dispatcher.register(EchoPlugin())
            engine.submit(self.request("EXEC-1"))
            engine.submit(self.request("EXEC-2"))
            records = engine.execute_all()
            self.assertEqual(
                tuple(r.execution_id for r in records),
                ("EXEC-1", "EXEC-2"),
            )

    def test_metrics_accumulate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            session.initialize()
            session.start()
            engine = ExecutionEngine(session=session)
            engine.dispatcher.register(EchoPlugin())
            engine.submit(self.request("EXEC-1"))
            engine.submit(self.request("EXEC-2"))
            engine.execute_all()
            self.assertEqual(engine.metrics.submitted_count, 2)
            self.assertEqual(engine.metrics.completed_count, 2)
            self.assertEqual(engine.metrics.succeeded_count, 2)
            self.assertEqual(engine.metrics.failed_count, 0)

    def test_missing_output_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            engine = ExecutionEngine(
                session=self.make_session(Path(temporary))
            )
            with self.assertRaises(ValidationError):
                engine.output("missing")

    def test_engine_snapshot_hash_stable_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            engine = ExecutionEngine(
                session=self.make_session(Path(temporary))
            )
            self.assertEqual(
                engine.snapshot_sha256,
                engine.snapshot_sha256,
            )

    def test_record_hash_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            session.initialize()
            session.start()
            engine = ExecutionEngine(session=session)
            engine.dispatcher.register(EchoPlugin())
            engine.submit(self.request())
            record = engine.execute_next()
            self.assertEqual(record.record_sha256, record.record_sha256)

    def test_scheduler_clear(self) -> None:
        scheduler = ExecutionScheduler()
        scheduler.submit(self.request("EXEC-1"))
        scheduler.submit(self.request("EXEC-2"))
        removed = scheduler.clear()
        self.assertEqual(len(removed), 2)
        self.assertEqual(scheduler.pending_count(), 0)


if __name__ == "__main__":
    unittest.main()
