from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from execution import ExecutionEngine
from kernel import (
    ConfigurationError,
    ExecutionContext,
    ValidationError,
)
from plugin_runtime import (
    CapabilityResolver,
    ManifestRegistry,
    PluginExecutionPipeline,
    PluginLifecycle,
    PluginLoader,
    PluginManifest,
    PluginState,
)
from runtime import RuntimeConfiguration, RuntimeSession


def manifest(
    plugin_id="echo",
    class_name="EchoPlugin",
    capabilities=("echo",),
    enabled=True,
    configuration=None,
):
    return PluginManifest(
        schema_version="1.0",
        plugin_id=plugin_id,
        plugin_version="1.0.0",
        module="tests.fixtures.b14_plugins",
        class_name=class_name,
        capabilities=capabilities,
        enabled=enabled,
        configuration=configuration or {},
    )


class PluginPipelineTests(unittest.TestCase):
    def make_session(self, root: Path) -> RuntimeSession:
        context = ExecutionContext.create(
            benchmark_id="pipeline-test",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version="2.0.0-phase-b1.4",
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B14-TEST",
            created_utc="2026-07-31T22:30:00.000000Z",
        )
        session = RuntimeSession(
            context=context,
            configuration=RuntimeConfiguration.empty(),
        )
        session.initialize()
        session.start()
        return session

    def test_manifest_hash_is_stable(self):
        self.assertEqual(
            manifest().manifest_sha256,
            manifest().manifest_sha256,
        )

    def test_manifest_capabilities_are_sorted_unique(self):
        value = manifest(capabilities=("z", "a", "z"))
        self.assertEqual(value.capabilities, ("a", "z"))

    def test_manifest_requires_capability(self):
        with self.assertRaises(ConfigurationError):
            manifest(capabilities=())

    def test_manifest_configuration_is_immutable(self):
        value = manifest(configuration={"x": 1})
        with self.assertRaises(TypeError):
            value.configuration["x"] = 2

    def test_registry_register_and_resolve(self):
        registry = ManifestRegistry()
        value = manifest()
        registry.register(value)
        self.assertIs(registry.resolve("echo"), value)

    def test_registry_duplicate_rejected(self):
        registry = ManifestRegistry()
        registry.register(manifest())
        with self.assertRaises(ConfigurationError):
            registry.register(manifest())

    def test_registry_load_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plugins.json"
            path.write_text(
                json.dumps({"plugins": [manifest().to_dict()]}),
                encoding="utf-8",
            )
            registry = ManifestRegistry()
            loaded = registry.load_file(path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(registry.registered_ids(), ("echo",))

    def test_resolver_single_candidate(self):
        registry = ManifestRegistry()
        registry.register(manifest())
        self.assertEqual(
            CapabilityResolver(registry).resolve("echo").plugin_id,
            "echo",
        )

    def test_resolver_missing_capability(self):
        with self.assertRaises(ConfigurationError):
            CapabilityResolver(ManifestRegistry()).resolve("missing")

    def test_resolver_ambiguous_capability(self):
        registry = ManifestRegistry()
        registry.register(manifest("echo-a"))
        registry.register(manifest("echo-b"))
        with self.assertRaises(ConfigurationError):
            CapabilityResolver(registry).resolve("echo")

    def test_resolver_preferred_candidate(self):
        registry = ManifestRegistry()
        registry.register(manifest("echo-a"))
        registry.register(manifest("echo-b"))
        resolved = CapabilityResolver(registry).resolve(
            "echo",
            preferred_plugin_id="echo-b",
        )
        self.assertEqual(resolved.plugin_id, "echo-b")

    def test_loader_loads_and_caches(self):
        loader = PluginLoader()
        first = loader.load(manifest())
        second = loader.load(manifest())
        self.assertIs(first, second)

    def test_loader_rejects_disabled(self):
        with self.assertRaises(ConfigurationError):
            PluginLoader().load(manifest(enabled=False))

    def test_loader_rejects_wrong_id(self):
        with self.assertRaises(ConfigurationError):
            PluginLoader().load(
                manifest(
                    plugin_id="expected",
                    class_name="WrongIdPlugin",
                )
            )

    def test_loader_rejects_invalid_protocol(self):
        with self.assertRaises(ConfigurationError):
            PluginLoader().load(
                manifest(
                    plugin_id="invalid",
                    class_name="InvalidPlugin",
                )
            )

    def test_lifecycle_happy_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            plugin = PluginLoader().load(manifest())
            lifecycle = PluginLifecycle("echo")
            lifecycle.loaded()
            self.assertTrue(
                lifecycle.health_check(plugin, session.context)
            )
            self.assertEqual(lifecycle.state, PluginState.READY)

    def test_lifecycle_invalid_transition(self):
        lifecycle = PluginLifecycle("echo")
        with self.assertRaises(ValidationError):
            lifecycle.close(type("P", (), {})())

    def test_pipeline_execute(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(
                manifest(configuration={"prefix": "prime"})
            )
            pipeline = PluginExecutionPipeline(engine, registry)
            record = pipeline.execute(
                execution_id="EXEC-B14-1",
                capability="echo",
                payload={"value": 101},
            )
            self.assertTrue(record.success)
            self.assertEqual(
                engine.output("EXEC-B14-1")["prefix"],
                "prime",
            )

    def test_pipeline_adds_manifest_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(manifest())
            pipeline = PluginExecutionPipeline(engine, registry)
            request = pipeline.submit(
                execution_id="EXEC-B14-2",
                capability="echo",
                payload={},
            )
            self.assertEqual(
                request.metadata["capability"],
                "echo",
            )
            self.assertEqual(
                len(request.metadata["manifest_sha256"]),
                64,
            )

    def test_pipeline_rejects_unhealthy_plugin(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(
                manifest(
                    plugin_id="unhealthy",
                    class_name="UnhealthyPlugin",
                    capabilities=("bad",),
                )
            )
            pipeline = PluginExecutionPipeline(engine, registry)
            with self.assertRaises(ConfigurationError):
                pipeline.submit(
                    execution_id="EXEC-B14-3",
                    capability="bad",
                    payload={},
                )

    def test_pipeline_close_plugin(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(manifest())
            pipeline = PluginExecutionPipeline(engine, registry)
            pipeline.activate("echo")
            pipeline.close_plugin("echo")
            self.assertEqual(
                pipeline.lifecycle("echo").state,
                PluginState.CLOSED,
            )
            self.assertEqual(pipeline.loader.loaded_ids(), ())

    def test_pipeline_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = self.make_session(Path(temporary))
            engine = ExecutionEngine(session=session)
            registry = ManifestRegistry()
            registry.register(manifest())
            pipeline = PluginExecutionPipeline(engine, registry)
            pipeline.activate("echo")
            snapshot = pipeline.snapshot()
            self.assertEqual(
                snapshot["loaded_plugins"],
                ["echo"],
            )
            self.assertEqual(
                snapshot["lifecycles"]["echo"]["state"],
                "ready",
            )


if __name__ == "__main__":
    unittest.main()
