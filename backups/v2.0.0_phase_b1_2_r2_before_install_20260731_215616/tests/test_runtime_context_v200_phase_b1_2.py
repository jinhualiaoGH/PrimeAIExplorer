from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from kernel import (
    ConfigurationError,
    ExecutionContext,
    ExecutionResult,
    KernelEvent,
    KernelEventType,
    RunnerError,
    ValidationError,
)
from runtime import (
    EventBus,
    RuntimeConfiguration,
    RuntimeSession,
    RuntimeState,
    ServiceRegistry,
)


class RuntimeContextTests(unittest.TestCase):
    def make_context(self, root: Path) -> ExecutionContext:
        return ExecutionContext.create(
            benchmark_id="prime_value",
            benchmark_version="2.0.0",
            connector_id="mock",
            software_version="2.0.0-phase-b1.2",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B12-TEST",
            created_utc="2026-07-31T12:00:00.000000Z",
        )

    def test_empty_configuration(self) -> None:
        config = RuntimeConfiguration.empty()
        self.assertEqual(dict(config.values), {})

    def test_configuration_from_mapping(self) -> None:
        config = RuntimeConfiguration.from_mapping({"mode": "test"})
        self.assertEqual(config.require("mode"), "test")

    def test_configuration_requires_key(self) -> None:
        config = RuntimeConfiguration.empty()
        with self.assertRaises(ConfigurationError):
            config.require("missing")

    def test_configuration_hash_stable(self) -> None:
        one = RuntimeConfiguration.from_mapping({"b": 2, "a": 1})
        two = RuntimeConfiguration.from_mapping({"a": 1, "b": 2})
        self.assertEqual(
            one.configuration_sha256,
            two.configuration_sha256,
        )

    def test_configuration_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "runtime.json"
            path.write_text(
                json.dumps({"mode": "file"}),
                encoding="utf-8",
            )
            config = RuntimeConfiguration.from_json_file(path)
            self.assertEqual(config.require("mode"), "file")

    def test_registry_register_and_resolve(self) -> None:
        registry = ServiceRegistry()
        service = object()
        registry.register("service", service)
        self.assertIs(registry.resolve("service"), service)

    def test_registry_duplicate_rejected(self) -> None:
        registry = ServiceRegistry()
        registry.register("service", object())
        with self.assertRaises(ConfigurationError):
            registry.register("service", object())

    def test_registry_ids_sorted(self) -> None:
        registry = ServiceRegistry()
        registry.register("z", object())
        registry.register("a", object())
        self.assertEqual(registry.registered_ids(), ("a", "z"))

    def test_registry_replace(self) -> None:
        registry = ServiceRegistry()
        first = object()
        second = object()
        registry.register("service", first)
        registry.register("service", second, replace=True)
        self.assertIs(registry.resolve("service"), second)

    def test_event_bus_publish(self) -> None:
        bus = EventBus()
        received = []

        def handler(event: KernelEvent) -> None:
            received.append(event.event_type)

        bus.subscribe("run_created", handler)
        event = KernelEvent(
            schema_version="1.0",
            session_id="RUN",
            event_type=KernelEventType.RUN_CREATED,
            sequence=1,
            occurred_utc="2026-07-31T12:00:00+00:00",
            detail={},
        )
        bus.publish(event)
        self.assertEqual(received, [KernelEventType.RUN_CREATED])

    def test_event_bus_duplicate_handler_rejected(self) -> None:
        bus = EventBus()

        def handler(event: KernelEvent) -> None:
            return None

        bus.subscribe("run_created", handler)
        with self.assertRaises(ConfigurationError):
            bus.subscribe("run_created", handler)

    def test_event_handler_failure_wrapped(self) -> None:
        bus = EventBus()

        def handler(event: KernelEvent) -> None:
            raise RuntimeError("boom")

        bus.subscribe("run_created", handler)
        event = KernelEvent(
            schema_version="1.0",
            session_id="RUN",
            event_type=KernelEventType.RUN_CREATED,
            sequence=1,
            occurred_utc="2026-07-31T12:00:00+00:00",
            detail={},
        )
        with self.assertRaises(RunnerError):
            bus.publish(event)

    def test_session_initial_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = RuntimeSession(
                context=self.make_context(Path(temporary)),
                configuration=RuntimeConfiguration.empty(),
            )
            self.assertIs(session.state, RuntimeState.CREATED)
            self.assertEqual(len(session.events.history()), 1)

    def test_session_success_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = self.make_context(Path(temporary))
            session = RuntimeSession(
                context=context,
                configuration=RuntimeConfiguration.empty(),
            )
            session.initialize()
            session.start()
            session.finish(
                ExecutionResult.success(
                    session_id=context.session_id,
                    elapsed_seconds=0.1,
                )
            )
            self.assertIs(session.state, RuntimeState.FINISHED)
            self.assertEqual(len(session.events.history()), 5)

    def test_invalid_transition_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = RuntimeSession(
                context=self.make_context(Path(temporary)),
                configuration=RuntimeConfiguration.empty(),
            )
            with self.assertRaises(ValidationError):
                session.start()

    def test_result_session_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = RuntimeSession(
                context=self.make_context(Path(temporary)),
                configuration=RuntimeConfiguration.empty(),
            )
            session.initialize()
            session.start()
            with self.assertRaises(ValidationError):
                session.finish(
                    ExecutionResult.success(
                        session_id="OTHER",
                        elapsed_seconds=0.1,
                    )
                )

    def test_session_failure_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = RuntimeSession(
                context=self.make_context(Path(temporary)),
                configuration=RuntimeConfiguration.empty(),
            )
            session.initialize()
            session.fail("failure")
            self.assertIs(session.state, RuntimeState.FAILED)
            self.assertEqual(
                session.events.history()[-1].event_type,
                KernelEventType.RUN_FAILED,
            )

    def test_close_after_finish(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = self.make_context(Path(temporary))
            session = RuntimeSession(
                context=context,
                configuration=RuntimeConfiguration.empty(),
            )
            session.initialize()
            session.start()
            session.finish(
                ExecutionResult.success(
                    session_id=context.session_id,
                    elapsed_seconds=0.1,
                )
            )
            session.close()
            self.assertIs(session.state, RuntimeState.CLOSED)

    def test_snapshot_hash_stable_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = RuntimeSession(
                context=self.make_context(Path(temporary)),
                configuration=RuntimeConfiguration.empty(),
            )
            one = session.snapshot_sha256
            two = session.snapshot_sha256
            self.assertEqual(one, two)


if __name__ == "__main__":
    unittest.main()
