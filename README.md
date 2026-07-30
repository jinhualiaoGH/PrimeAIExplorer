# PrimeAIExplorer v0.2

PrimeAIExplorer v0.2 is a plugin-based numerical continuation benchmark.

## Architecture

```text
PrimeNet Repository
        ↓
Sequence Plugins
        ↓
Unified Case Generator
        ↓
Unified Prompt Generator
        ↓
GPT / Claude / Gemini / Other Models
        ↓
Unified Response Scorer
        ↓
Reports
```

## Included sequence plugins

- `prime_gap`
- `left_twin`

## Repository paths

The default PrimeNet paths are:

```text
E:\PrimeNet\Repository\ranges
E:\PrimeNet\Repository\gaps_u16
```

Edit the experiment configuration files if your repository differs.

## Installation

Extract the package, then run:

```powershell
cd C:\Downloads\PrimeAIExplorer_v0.2
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install_v0.2.ps1
```

Default destination:

```text
C:\PrimeAIExplorer
```

## Validate installation

```powershell
cd C:\PrimeAIExplorer
py .\scripts\doctor.py
py -m unittest discover -s .\tests -v
```

## EXP-000001 — Prime-gap continuation

```powershell
py .\run_experiment.py validate `
    --config .\experiments\EXP-000001\config\experiment.json

py .\run_experiment.py generate-cases `
    --config .\experiments\EXP-000001\config\experiment.json

py .\run_experiment.py generate-prompts `
    --config .\experiments\EXP-000001\config\experiment.json
```

## EXP-000002 — Left-twin-prime continuation

```powershell
py .\run_experiment.py validate `
    --config .\experiments\EXP-000002\config\experiment.json

py .\run_experiment.py build-dataset `
    --config .\experiments\EXP-000002\config\experiment.json

py .\run_experiment.py generate-cases `
    --config .\experiments\EXP-000002\config\experiment.json

py .\run_experiment.py generate-prompts `
    --config .\experiments\EXP-000002\config\experiment.json
```

## Response format

```json
{
  "prediction": 123,
  "confidence": 50,
  "explanation": "Brief explanation."
}
```

Save responses under:

```text
experiments\EXP-00000X\responses\<model>\
```

The filename must equal the case ID:

```text
CASE-000001.json
```

Then score:

```powershell
py .\run_experiment.py score `
    --config .\experiments\EXP-000002\config\experiment.json
```
