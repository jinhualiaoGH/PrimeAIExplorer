# PrimeAIExplorer v0.2.5

PrimeAIExplorer v0.2.5 adds the **Collection Assistant** to the partial-pilot manager and scientific response observatory.

## New in v0.2.5

- `collect` validates and atomically commits one response into `responses.json`.
- Uses `current_response.json` by default, while analysis discovery ignores that working file.
- Selects the first pending ledger entry automatically or accepts `--case-id`.
- Creates a timestamped backup before every commit.
- Refuses to overwrite completed responses.
- Clears the working file after a successful commit unless `--keep-working-file` is used.
- Reports completed, pending, progress, and the next unfinished case.
- Supports `--dry-run` and direct `--response-json` input.

## Install

```powershell
cd C:\PrimeAIExplorer\release\PrimeAIExplorer_v0_2_5
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

## Test and demo

```powershell
.\run_tests.ps1
.\run_demo.ps1
```

## Standard collection cycle

Put a model response in:

```text
pilot_002\current_response.json
```

Then commit it:

```powershell
.\.venv\Scripts\paiexp.exe collect `
    --responses "C:\PrimeAIExplorer\experiments\exp000001\pilot_002" `
    --dataset "C:\PrimeAIExplorer\experiments\exp000001\dataset\cases.csv" `
    --model "GPT-5.6 Thinking"
```

The command validates the response, backs up the ledger, commits it to the next pending case, clears the working file, and prints progress.
