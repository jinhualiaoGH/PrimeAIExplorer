# PrimeAIExplorer Architecture Specification v1.0

This package establishes the architectural foundation for PrimeAIExplorer v1.0.

It does not replace the current working codebase. It adds documentation, schemas,
templates, and validation scripts that guide controlled future refactoring.

## Contents

```text
docs/
    Architecture.md
    Module_Ownership.md
    Sequence_Plugin_API.md
    Connector_API.md
    Experiment_Format.md
    Evaluation_Contract.md
    Reproducibility_Contract.md
    Versioning_Policy.md
    Roadmap.md

schemas/
    experiment.schema.json
    connector_registry.schema.json
    run_manifest.schema.json

templates/
    sequence_plugin_template.py
    connector_plugin_template.py
    evaluation_plugin_template.py

scripts/
    install_architecture_spec.ps1
    validate_architecture_spec.py
```

## Installation

```powershell
cd C:\Downloads\PrimeAIExplorer_Architecture_Spec_v1.0

Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass

.\scripts\install_architecture_spec.ps1
```

Default destination:

```text
C:\PrimeAIExplorer
```

The installer creates or updates:

```text
C:\PrimeAIExplorer\docs
C:\PrimeAIExplorer\schemas
C:\PrimeAIExplorer\templates
```

It does not delete or replace the existing `core`, `connectors`, `plugins`,
`experiments`, or `tests` directories.
