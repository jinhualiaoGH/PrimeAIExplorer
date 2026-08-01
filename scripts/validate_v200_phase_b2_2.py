from __future__ import annotations

from pathlib import Path
import sys
import tempfile

import numpy as np

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
from sequence_api import file_sha256


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<35} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    version = (ROOT / "VERSION").read_text(
        encoding="utf-8"
    ).strip()

    print("PrimeAIExplorer v2.0 Phase B2.2 Validator")
    print("=" * 92)
    check(
        "installed version",
        version == "2.0.0-phase-b2.2-r3",
        version,
    )

    with tempfile.TemporaryDirectory() as temporary:
        data_root = Path(temporary)
        source = data_root / "prime_values.npy"
        np.save(
            source,
            np.array([2, 3, 5, 7, 11, 13], dtype=np.uint64),
        )
        source_hash = file_sha256(source)

        context = ExecutionContext.create(
            benchmark_id="b22-validation",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version=version,
            project_root=data_root,
            working_directory=data_root / "work",
            output_directory=data_root / "output",
            configuration={},
            session_id="RUN-B22-VALIDATION",
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
                ),
                enabled=True,
                configuration={
                    "providers": [
                        {
                            "provider_type": "numpy_npy_memmap",
                            "sequence_id": "prime-value",
                            "source_path": "prime_values.npy",
                            "title": "Prime values",
                            "index_origin": 1,
                            "strictly_increasing": True,
                            "expected_sha256": source_hash,
                        }
                    ]
                },
            )
        )

        engine = ExecutionEngine(session=session)
        pipeline = PluginExecutionPipeline(engine, registry)

        descriptor_record = pipeline.execute(
            execution_id="EXEC-B22-DESCRIBE",
            capability="sequence.describe",
            payload={
                "operation": "describe",
                "sequence_id": "prime-value",
            },
        )
        descriptor = engine.output("EXEC-B22-DESCRIBE")

        window_record = pipeline.execute(
            execution_id="EXEC-B22-WINDOW",
            capability="sequence.window",
            payload={
                "operation": "window",
                "sequence_id": "prime-value",
                "start_index": 3,
                "count": 3,
            },
        )
        window = engine.output("EXEC-B22-WINDOW")

        plugin = pipeline.loader.load(
            registry.resolve("sequence_api")
        )
        provider = plugin.registry.resolve("prime-value")

        check(
            "memmap plugin loaded",
            pipeline.loader.loaded_ids() == ("sequence_api",),
            "sequence_api",
        )
        check(
            "provider implementation",
            type(provider).__name__ == "NpyMemmapSequenceProvider",
            type(provider).__name__,
        )
        check(
            "descriptor execution",
            descriptor_record.success,
            descriptor["sequence_id"],
        )
        check(
            "memory mapped",
            descriptor["metadata"]["memory_mapped"] is True,
            "true",
        )
        check(
            "read only",
            provider._array.flags.writeable is False,
            "true",
        )
        check(
            "source identity",
            descriptor["metadata"]["file_identity"]["file_sha256"]
            == source_hash,
            source_hash[:16],
        )
        check(
            "dtype",
            descriptor["metadata"]["file_identity"]["dtype"]
            == "<u8",
            descriptor["metadata"]["file_identity"]["dtype"],
        )
        check(
            "window execution",
            window_record.success,
            window_record.output_sha256[:16],
        )
        check(
            "window values",
            window["values"] == [5, 7, 11],
            str(window["values"]),
        )
        check(
            "index contract",
            window["start_index"] == 3
            and window["end_index"] == 5,
            "3..5",
        )

        pipeline.close_plugin("sequence_api")
        check(
            "mapping lifecycle",
            provider.is_open is False,
            "closed",
        )

        # Release validator references before TemporaryDirectory attempts
        # removal. This is required on Windows, where open mmap handles block
        # deletion of the mapped .npy file.
        import gc
        del provider
        del plugin
        del pipeline
        del engine
        del registry
        del session
        gc.collect()

    print("=" * 92)
    print("PrimeAIExplorer v2.0 Phase B2.2 Revision 3 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
