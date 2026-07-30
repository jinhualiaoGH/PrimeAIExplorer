from __future__ import annotations

import json
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = (
    "Architecture.md",
    "Module_Ownership.md",
    "Sequence_Plugin_API.md",
    "Connector_API.md",
    "Experiment_Format.md",
    "Evaluation_Contract.md",
    "Reproducibility_Contract.md",
    "Versioning_Policy.md",
    "Roadmap.md",
)

REQUIRED_SCHEMAS = (
    "experiment.schema.json",
    "connector_registry.schema.json",
    "run_manifest.schema.json",
)

REQUIRED_TEMPLATES = (
    "sequence_plugin_template.py",
    "connector_plugin_template.py",
    "evaluation_plugin_template.py",
)


def check(label: str, condition: bool, detail: str) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<24} {detail}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    print("PrimeAIExplorer Architecture Specification Validator")
    print("=" * 76)

    for name in REQUIRED_DOCS:
        path = ROOT / "docs" / name
        check("Documentation", path.exists() and path.stat().st_size > 0, str(path))

    for name in REQUIRED_SCHEMAS:
        path = ROOT / "schemas" / name
        with path.open("r", encoding="utf-8") as f:
            value = json.load(f)
        check("JSON schema", isinstance(value, dict), str(path))

    for name in REQUIRED_TEMPLATES:
        path = ROOT / "templates" / name
        py_compile.compile(str(path), doraise=True)
        check("Python template", True, str(path))

    print("=" * 76)
    print("Architecture specification validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
