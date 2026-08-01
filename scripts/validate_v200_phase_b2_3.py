from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from execution import ExecutionEngine
from kernel import ExecutionContext
from plugin_runtime import ManifestRegistry, PluginExecutionPipeline, PluginManifest
from runtime import RuntimeConfiguration, RuntimeSession
from sequence_api import file_sha256


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<36} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    print("PrimeAIExplorer v2.0 Phase B2.3 Validator")
    print("=" * 94)
    check("installed version", version == "2.0.0-phase-b2.3", version)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        values = ((2, 4, 2), (6, 6, 8), (4, 2, 10))
        partitions = []
        cursor = 1
        for ordinal, data in enumerate(values):
            path = root / f"gaps_{ordinal:03d}.npy"
            np.save(path, np.asarray(data, dtype=np.uint16))
            partitions.append({
                "ordinal": ordinal,
                "start_index": cursor,
                "count": len(data),
                "path": path.name,
                "sha256": file_sha256(path),
            })
            cursor += len(data)
        (root / "gap_manifest.json").write_text(
            json.dumps({
                "schema_version": "1.0",
                "repository_id": "validation-gap-repository",
                "repository_version": "1.0.0",
                "dtype": "uint16",
                "index_origin": 1,
                "partitions": partitions,
                "metadata": {"ownership": "left-owned outgoing gap"},
            }, indent=2),
            encoding="utf-8",
        )

        context = ExecutionContext.create(
            benchmark_id="b23-validation",
            benchmark_version="1.0.0",
            connector_id="local",
            software_version=version,
            project_root=root,
            working_directory=root / "work",
            output_directory=root / "output",
            configuration={},
            session_id="RUN-B23-VALIDATION",
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
                capabilities=("sequence.describe", "sequence.window"),
                enabled=True,
                configuration={
                    "providers": [{
                        "provider_type": "partitioned_gap_uint16",
                        "sequence_id": "prime-gap",
                        "manifest_path": "gap_manifest.json",
                        "cache_size": 2,
                        "verify_partition_sha256": True,
                    }]
                },
            )
        )
        engine = ExecutionEngine(session=session)
        pipeline = PluginExecutionPipeline(engine, registry)
        try:
            descriptor_record = pipeline.execute(
                execution_id="EXEC-B23-DESCRIBE",
                capability="sequence.describe",
                payload={"operation": "describe", "sequence_id": "prime-gap"},
            )
            window_record = pipeline.execute(
                execution_id="EXEC-B23-WINDOW",
                capability="sequence.window",
                payload={
                    "operation": "window",
                    "sequence_id": "prime-gap",
                    "start_index": 3,
                    "count": 5,
                },
            )
            descriptor = engine.output("EXEC-B23-DESCRIBE")
            window = engine.output("EXEC-B23-WINDOW")
            plugin = pipeline.loader.load(registry.resolve("sequence_api"))
            provider = plugin.registry.resolve("prime-gap")

            check("gap plugin loaded", pipeline.loader.loaded_ids() == ("sequence_api",), "sequence_api")
            check("provider implementation", type(provider).__name__ == "PartitionedGapSequenceProvider", type(provider).__name__)
            check("descriptor execution", descriptor_record.success, descriptor["sequence_id"])
            check("repository dtype", descriptor["metadata"]["repository_dtype"] == "uint16", descriptor["metadata"]["repository_dtype"])
            check("partition count", descriptor["metadata"]["partition_count"] == 3, str(descriptor["metadata"]["partition_count"]))
            check("manifest identity", len(descriptor["metadata"]["manifest_sha256"]) == 64, descriptor["metadata"]["manifest_sha256"][:16])
            check("cross-partition window", window_record.success, window_record.output_sha256[:16])
            check("window values", window["values"] == [2, 6, 6, 8, 4], str(window["values"]))
            check("index contract", window["start_index"] == 3 and window["end_index"] == 7, "3..7")
            check("cache bound", provider.open_partition_count <= 2, str(provider.open_partition_count))
        finally:
            pipeline.close_plugin("sequence_api")

        check("mapping lifecycle", provider.open_partition_count == 0, "closed")

    print("=" * 94)
    print("PrimeAIExplorer v2.0 Phase B2.3 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
